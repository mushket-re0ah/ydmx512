from kivy.utils import platform


if platform == "win":
    # https://stackoverflow.com/questions/67121032/make-usb-device-visible-with-different-vendor-and-product-id

    import struct

    import win32api
    import win32file
    import pywintypes


    def CTL_CODE(DeviceType, Function, Method, Access):
        return (DeviceType << 16) | (Access << 14) | (Function << 2) | Method
    def USB_CTL(id):
       # CTL_CODE(FILE_DEVICE_USB, (id), METHOD_BUFFERED, FILE_ANY_ACCESS)
        return CTL_CODE(0x22, id, 0, 0)


    IOCTL_USB_GET_ROOT_HUB_NAME = USB_CTL(258)                   # HCD_GET_ROOT_HUB_NAME
    IOCTL_USB_GET_NODE_INFORMATION = USB_CTL(258)                # USB_GET_NODE_INFORMATION
    IOCTL_USB_GET_NODE_CONNECTION_INFORMATION = USB_CTL(259)     # USB_GET_NODE_CONNECTION_INFORMATION
    IOCTL_USB_GET_NODE_CONNECTION_DRIVERKEY_NAME = USB_CTL(264)  # USB_GET_NODE_CONNECTION_DRIVERKEY_NAME
    IOCTL_USB_GET_NODE_CONNECTION_NAME = USB_CTL(261)            # USB_GET_NODE_CONNECTION_NAME
    IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION = USB_CTL(260) # USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION

    USB_CONFIGURATION_DESCRIPTOR_TYPE = 2
    USB_STRING_DESCRIPTOR_TYPE = 3
    USB_INTERFACE_DESCRIPTOR_TYPE = 4
    MAXIMUM_USB_STRING_LENGTH = 255


    def open_dev(name):
        try:
            handle = win32file.CreateFile(name,
                                      win32file.GENERIC_WRITE,
                                      win32file.FILE_SHARE_WRITE,
                                      None,
                                      win32file.OPEN_EXISTING,
                                      0,
                                      None)
        except pywintypes.error as e:
            return None
        return handle


    def get_root_hub_name(handle):
        buf = win32file.DeviceIoControl(handle,
                                    IOCTL_USB_GET_ROOT_HUB_NAME,
                                    None,
                                    6,
                                    None)
        act_len, _ = struct.unpack('LH', buf)
        buf = win32file.DeviceIoControl(handle,
                                    IOCTL_USB_GET_ROOT_HUB_NAME,
                                    None,
                                    act_len,
                                    None)
        return buf[4:].decode('utf-16le')


    def get_ext_hub_name(handle, index):
        hub_name = chr(index) + '\0'*9
        buf = win32file.DeviceIoControl(handle,
                                    IOCTL_USB_GET_NODE_CONNECTION_NAME,
                                    bytes(hub_name, "utf-8"),
                                    10,
                                    None)
        _, act_len, _ = struct.unpack('LLH', buf)
        buf = win32file.DeviceIoControl(handle,
                                    IOCTL_USB_GET_NODE_CONNECTION_NAME,
                                    bytes(hub_name, "utf-8"),
                                    act_len,
                                    None)
        return buf[8:].decode('utf-16le')


    def get_str_desc(handle, conn_idx, str_idx):
        req = struct.pack('LBBHHH',
                      conn_idx,
                      0,
                      0,
                      (USB_STRING_DESCRIPTOR_TYPE<<8) | str_idx,
                      win32api.GetSystemDefaultLangID(),
                      MAXIMUM_USB_STRING_LENGTH)
        try:
            buf = win32file.DeviceIoControl(handle,
                                        IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION,
                                        req,
                                        12+MAXIMUM_USB_STRING_LENGTH,
                                        None)
        except pywintypes.error as e:
             return 'ERROR: no String Descriptor for index {}'.format(str_idx)
        if len(buf) > 16:
            return buf[14:].decode('utf-16le')
        return ''


    def exam_hub(name, level, usb_port) -> str:
        handle = open_dev(r'\\.\{}'.format(name))
        if not handle:
            print('Failed to open device {}'.format(name))
            return
        buf = win32file.DeviceIoControl(handle,
                                    IOCTL_USB_GET_NODE_INFORMATION,
                                    None,
                                    76,
                                    None)
        product_name = print_hub_ports(handle, buf[6], level, usb_port)
        handle.close()
        return product_name


    def print_hub_ports(handle, num_ports, level, usb_port) -> str:
        for idx in range(1, num_ports+1):
            info = bytes(chr(idx) + '\0'*34, 'utf-8')
            try:
                buf = win32file.DeviceIoControl(handle,
                                            IOCTL_USB_GET_NODE_CONNECTION_INFORMATION,
                                            info,
                                            34 + 11*30,
                                            None)
            except pywintypes.error as e:
                print(e)
                print(e.winerror, e.funcname, e.strerror)
                return
            _, vid, pid, vers, manu, prod, seri, _, ishub, _, stat = struct.unpack('=12sHHHBBB3s?6sL', buf[:35])

            if ishub:
                product_name = exam_hub(get_ext_hub_name(handle, idx), level, usb_port)
                return product_name
            elif (stat == 1) and (prod != 0) and (idx == usb_port):
                return get_str_desc(handle, idx, prod)


    def get_product_name_by_port(port: "list_ports.comports") -> [str, None]:
        # usb_location - location из serial.tools.list_ports_common.ListPortInfo
        usb_location = port.location
        if usb_location is None:
            return None
        usb_port = int(usb_location.split(":x")[0].split('.')[-1].split('-')[-1])

        for i in range(10):
            name = r"\\.\HCD{}".format(i)
            handle = open_dev(name)
            if not handle:
                continue

            root = get_root_hub_name(handle)

            dev_name = r'\\.\{}'.format(root)
            dev_handle = open_dev(dev_name)
            if not dev_handle:
                print('Failed to open device {}'.format(dev_name))
                continue

            buf = win32file.DeviceIoControl(dev_handle,
                                        IOCTL_USB_GET_NODE_INFORMATION,
                                        None,
                                        76,
                                        None)
            product_name = print_hub_ports(dev_handle, buf[6], 0, usb_port)
            dev_handle.close()
            handle.close()
            if product_name is not None:
                return product_name

elif platform == "macosx":
    def get_product_name_by_port(port: "list_ports.comports") -> [str, None]:
        return port.product

elif platform == "linux":
    def get_product_name_by_port(port: "list_ports.comports") -> [str, None]:
        return port.product
else:
    raise ImportError(f"Нет реализации для данной платформы: {platform}")
