#include <inttypes.h>
#include <Arduino.h>
#include <DmxSimple.h>
#include <string.h>
#include <avr/wdt.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>

struct {
    char magic[5] = {'S', 'A', 'M', 'P', 'O'};
    uint8_t device_type = 0;
    uint8_t major_version = 0;
    uint8_t minor_version = 0;
    uint8_t patch_version = 0;
    uint8_t protocol_version = 0;
} IDENTIFY;

/*
    Как в целом работает вся эта шляпа?
    Есть 2 режима работы - ожидание (waiting) и прием сообщений (serial).
      Вообще, возможно, добавится еще связь по LAN, и прием сообщений придется
    немного переделать. Но пока это Serial.
      В режиме ожидания мы отправляем handshake пакеты, пока комп не прочтет их
    и не отправит нам ответ. Далее мы читаем ответ, и если все хорошо, то
    переходим в режим приема сообщений.
      В режиме приема сообщений мы ждем, когда придет сообщение. Читается оно
    последовательно, т.к. на контроллере банально нет столько памяти, чтобы
    куда-то его буферизировать. Далее сообщение разбирается, читаются метаданные,
    проверяется crc8, дальше разбираются полезные данные и отсылаются на DMX,
    при этом проверяя валидность адресов и удачно ли проходит чтение.
      Во время того, как мы находимся в режиме приема сообщений, то если в
    течении 10 секунд от хоста нет сообщений, то мы выходим из режима приема
    сообщений.
      Хост не отправляет новое сообщение, пока мы не уведомим его, что прочли
    прошлое.


    # FIX
    ШТОРМ НЕУТИХАЕТ
      А если двусторонний handshake, инициируемый хостом? Это изменит
    парадигму: контроллер не будет спамить SAMPO по таймеру, а будет отвечать
    SAMPO только когда хост явно попросит. Это устранит накопление данных в
    буфере драйвера при простое, потому что в буфер будут попадать только
    ответы на запросы хоста, которые хост сразу же читает. В режиме ожидания
    контроллер просто слушает входящие байты. Если приходят любые данные,
    необязательно handshake, то тогда контроллер отправляет SAMPO и ждет
    полноценного SAMPO от хоста. После получения SAMPO от хоста контроллер
    переходит в serial режим. По сути, это тройное рукопожатие:
    host ping -> device SAMPO -> host SAMPO -> device serial mode.
*/


class SerialUtils {
private:
    static bool read_error;

    static inline void reset_read_error() {
        read_error = false;
    }

    static inline void set_read_error() {
        read_error = true;
    }
public:
    static inline void clear_buffer() {
        while (Serial.available()) {
            Serial.read();
        }
    }

    static inline bool has_read_error() {
        return read_error;
    }

    static inline void read(void* buf, size_t buf_len) {
        reset_read_error();
        size_t actual = Serial.readBytes(static_cast<uint8_t*>(buf), buf_len);
        if (actual != buf_len) {
            set_read_error();
            clear_buffer();
        }
    }

    static inline uint8_t read_uint8() {
        uint8_t buf;
        read(&buf, sizeof(buf));
        return buf;
    }

    static inline uint16_t read_uint16() {
        uint16_t buf;
        read(&buf, sizeof(buf));
        return buf;
    }

    //   В методах записи flush нужен для синхронизации и надежности, хост не
    // отправит сообщение пока не получит ответ от контроллера
    // UPDATE: НАХУЙ FLUSH
    static inline void write(void* buf, size_t buf_len) {
        Serial.write(static_cast<const uint8_t*>(buf), buf_len);
    }

    static inline void write_uint8(uint8_t val) {
        Serial.write(val);
    }
};
static bool SerialUtils::read_error = false;


// ############################################################################
// ############################################################################
// #############################---CONNECTION---###############################
// ############################################################################
// ############################################################################


void reset_serial_packet_timeout();
class Connection {
private:
    static const char CONNECTION_MSG[];
    static const size_t CONNECTION_MSG_LEN;
    // static const uint32_t CONNECTION_MSG_TIME_INTERVAL_MS = 2500;

    // static uint32_t last_try_connection_time;
    static uint8_t match_index;

    enum class OperatingMode : uint8_t {
        WAITING_MODE = 0,
        SERIAL_MODE = 1
    };
    static volatile OperatingMode operating_mode;

    static bool check_serial_msg() {
        while (Serial.available() > 0) {
            char c = Serial.read();

            if (c == CONNECTION_MSG[match_index]) {
                match_index++;
                if (match_index == CONNECTION_MSG_LEN) {
                    match_index = 0;  // готовы к следующему поиску
                    return true;      // нашли SAMPO
                }
            } else {
                // символ не совпал, сбрасываем прогресс
                match_index = 0;
                // но если он совпал с первым символом, начинаем новый поиск
                if (c == CONNECTION_MSG[0]) {
                    match_index = 1;
                }
            }
        }
        return false;
    }

public:
    static inline void set_mode_serial() {
        reset_serial_packet_timeout();
        operating_mode = OperatingMode::SERIAL_MODE;
        match_index = 0;
    }

    static inline void set_mode_waiting() {
        operating_mode = OperatingMode::WAITING_MODE;
        // last_try_connection_time = millis();
        match_index = 0;
    }

    static void write_handshake_msg() {
        // if ((Serial.availableForWrite() >= CONNECTION_MSG_LEN) && !Serial.available()) {
        if (Serial.availableForWrite() >= CONNECTION_MSG_LEN) {
            SerialUtils::write(CONNECTION_MSG, CONNECTION_MSG_LEN);
            // last_try_connection_time = millis();
        }
    }

    // static void check_write_handshake_msg() {
    //     if ((millis() - last_try_connection_time) >= CONNECTION_MSG_TIME_INTERVAL_MS) {
    //         write_handshake_msg();
    //     }
    // }

    static inline void check_serial_connection() {
        if (check_serial_msg()) {
            write_handshake_msg();
            set_mode_serial();
        }
        // else {
        //     write_handshake_msg();
        //     // check_write_handshake_msg();
        // }
    }

    static inline bool if_mode_waiting() {
        return operating_mode == OperatingMode::WAITING_MODE;
    }

    static inline bool if_mode_serial() {
        return operating_mode == OperatingMode::SERIAL_MODE;
    }
};
static const char Connection::CONNECTION_MSG[] = "SAMPO";
static const size_t Connection::CONNECTION_MSG_LEN = sizeof(CONNECTION_MSG) - 1;
// static uint32_t Connection::last_try_connection_time = 0;
static uint8_t Connection::match_index = 0;
static volatile Connection::OperatingMode Connection::operating_mode = OperatingMode::WAITING_MODE;


// ############################################################################
// ############################################################################
// #################################---DMX---##################################
// ############################################################################
// ############################################################################


class DMXModule {
private:
    static const uint8_t PIN = 3;
public:
    static const int DMX_MIN_CHANNEL = 1;
    static const int DMX_MAX_CHANNEL = 512;
    static const uint8_t DMX_ADDRESS_512_SIZE = 2;
    static const uint8_t DMX_ADDRESS_256_SIZE = 1;
    static const uint8_t DMX_VALUE_SIZE = 1;
    static const uint8_t DMX_MSG_512_SIZE = DMX_ADDRESS_512_SIZE + DMX_VALUE_SIZE;
    static const uint8_t DMX_MSG_256_SIZE = DMX_ADDRESS_256_SIZE + DMX_VALUE_SIZE;
    static const uint8_t DMX_ADDRESS_LENGTH_512_SIZE = 2;
    static const uint8_t DMX_ADDRESS_LENGTH_256_SIZE = 1;
    static const uint16_t DMX_MAX_MSG_SIZE = DMX_MAX_CHANNEL * DMX_MSG_512_SIZE;
    static bool check_address(const uint16_t address) {
        return (address >= DMX_MIN_CHANNEL && address <= DMX_MAX_CHANNEL);
    }

    static void init() {
        DmxSimple.usePin(PIN);
        DmxSimple.maxChannel(DMX_MAX_CHANNEL);
    }
};


// ############################################################################
// ############################################################################
// #########################---MESSAGE PROCESSING---###########################
// ############################################################################
// ############################################################################


enum class DMXResultCode : uint8_t {
    SUCCESS = 0x00,
    TERMINATE_CONNECTION = 0x01,
    UNCORRECT_MSG_SIZE = 0x02,
    UNCORRECT_MSG_TYPE = 0x03,
    UNCORRECT_ADDRESS = 0x04,
    READ_ERROR = 0x05,
    READ_COUNT_ERROR = 0x06,
    ADDRESS_LENGHT_ERROR = 0x07,
    CRC_ERROR = 0x08,
    WATCHDOG_ERROR = 0x09
};


class MessageMetadata {
/*
Битовая структура заголовка:
  - Байт 0: CRC-8 от байтов 1-2
  - Байт 1 (младший): Биты 7-0 (часть размера)
  - Байт 2 (старший): Биты 15-8 (тип + флаг + часть размера)
*/

private:
    static const uint16_t MASK_TYPE = 0xF000;
    static const uint16_t MASK_IS_ADDRESS_1_BYTE = 0x0800;
    static const uint16_t MASK_SIZE = 0x07FF;
    static const int METADATA_SIZE = 3;
    static const uint16_t ERROR_METADATA = 0xFF00;
    static const uint8_t CRC_POLY = 0x07;
    static const uint8_t crc8_table[256] PROGMEM;

    static uint8_t compute_crc(uint8_t byte1, uint8_t byte2) {
        uint8_t crc = pgm_read_byte(&crc8_table[byte1]);
        return pgm_read_byte(&crc8_table[crc ^ byte2]);
    }

    enum class MessageType : uint8_t {
        TERMINATE_CONNECTION = 0x00,
        STANDARD = 0x01,
        ADDRESS_COMPRESS = 0x02,
        ADDRESS_VALUES_COMPRESS = 0x03
    };

    static MessageType _type;
    static bool _is_address_1_byte;
    static uint16_t _size;
public:
    enum class ReadMetadataResult : uint8_t {
        SUCCESS = 0x00,
        READ_ERROR = 0x01,
        CRC_ERROR = 0x02,
    };

    static ReadMetadataResult read_from_serial() {
        uint8_t buf[METADATA_SIZE];
        SerialUtils::read(buf, METADATA_SIZE);
        if (SerialUtils::has_read_error()) {
            return ReadMetadataResult::READ_ERROR;
        }
        uint8_t crc = compute_crc(buf[1], buf[2]);
        if (crc != buf[0]) {
            SerialUtils::clear_buffer();
            return ReadMetadataResult::CRC_ERROR;
        }
        uint16_t raw_metadata = (static_cast<uint16_t>(buf[2]) << 8) | buf[1];

        _type = MessageType((raw_metadata & MASK_TYPE) >> 12);
        _is_address_1_byte = (raw_metadata & MASK_IS_ADDRESS_1_BYTE) >> 11;
        _size = raw_metadata & MASK_SIZE;
        return ReadMetadataResult::SUCCESS;
    }

    inline static bool is_message_type_terminate() {
        return _type == MessageType::TERMINATE_CONNECTION;
    }

    inline static bool is_message_type_standard() {
        return _type == MessageType::STANDARD;
    }

    inline static bool is_message_type_address_compress() {
        return _type == MessageType::ADDRESS_COMPRESS;
    }

    inline static bool is_message_type_address_values_compress() {
        return _type == MessageType::ADDRESS_VALUES_COMPRESS;
    }

    inline static bool is_address_1_byte() {
        return _is_address_1_byte;
    }

    inline static uint16_t get_address_size() {
        return _is_address_1_byte ? DMXModule::DMX_ADDRESS_LENGTH_256_SIZE : DMXModule::DMX_ADDRESS_LENGTH_512_SIZE;
    }

    inline static uint16_t get_message_size() {
        return _is_address_1_byte ? DMXModule::DMX_MSG_256_SIZE : DMXModule::DMX_MSG_512_SIZE;
    }

    inline static uint16_t get_size() {
        return _size;
    }

    inline static bool available() {
        return Serial.available() >= METADATA_SIZE;
    }
};
static const uint8_t MessageMetadata::crc8_table[256] PROGMEM = {
    0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15, 0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d,
    0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65, 0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d,
    0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5, 0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
    0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85, 0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,
    0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2, 0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea,
    0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2, 0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
    0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32, 0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a,
    0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42, 0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a,
    0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c, 0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
    0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec, 0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4,
    0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c, 0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44,
    0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c, 0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
    0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b, 0x76, 0x71, 0x78, 0x7f, 0x6a, 0x6d, 0x64, 0x63,
    0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b, 0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13,
    0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb, 0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
    0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb, 0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3
};
static MessageMetadata::MessageType MessageMetadata::_type = MessageMetadata::MessageType::STANDARD;
static bool MessageMetadata::_is_address_1_byte = false;
static uint16_t MessageMetadata::_size = 0;


class DMXReader {
private:
    static volatile uint16_t bytes_readed;
    static DMXResultCode reader_state;

    static inline void reset_reader_state() {
        reader_state = DMXResultCode::SUCCESS;
    }
    static inline const uint16_t _read_address_data_1_or_2_bytes() {
        reset_reader_state();
        uint16_t address;
        if (MessageMetadata::is_address_1_byte()) {
            address = static_cast<uint16_t>(SerialUtils::read_uint8());
         } else {
            address = SerialUtils::read_uint16();
        }
        if (SerialUtils::has_read_error()) {
            reader_state = DMXResultCode::READ_ERROR;
        }
        else if (!DMXModule::check_address(address)) {
            reader_state = DMXResultCode::UNCORRECT_ADDRESS;
        }
        bytes_readed += MessageMetadata::get_address_size();
        return address;
    }
public:
    static inline const uint16_t read_address_length() {
        uint16_t address_length = _read_address_data_1_or_2_bytes();
        if (address_length == 0 || address_length > DMXModule::DMX_MAX_CHANNEL) {
            reader_state = DMXResultCode::ADDRESS_LENGHT_ERROR;
        }
        return address_length;
    }

    static inline const uint16_t read_count() {
        uint16_t count = _read_address_data_1_or_2_bytes();
        if (count == 0 || count > DMXModule::DMX_MAX_CHANNEL) {
            reader_state = DMXResultCode::READ_COUNT_ERROR;
        }
        return count;
    }

    static inline uint16_t read_address() {
        return _read_address_data_1_or_2_bytes();
    }

    static inline uint8_t read_value() {
        reset_reader_state();
        uint8_t value = SerialUtils::read_uint8();
        if (SerialUtils::has_read_error()) {
            reader_state = DMXResultCode::READ_ERROR;
        }
        bytes_readed += DMXModule::DMX_VALUE_SIZE;
        return value;
    }

    static inline void reset() {
        bytes_readed = 0;
    }

    static inline bool check_bytes_readed_success() {
        return bytes_readed == MessageMetadata::get_size();
    }

    static inline bool bytes_remaining() {
        return bytes_readed < MessageMetadata::get_size();
    }

    static inline bool has_read_error() {
        return reader_state != DMXResultCode::SUCCESS;
    }

    static inline DMXResultCode get_read_error() {
        return reader_state;
    }
};
static volatile uint16_t DMXReader::bytes_readed = 0;
static DMXResultCode DMXReader::reader_state = DMXResultCode::SUCCESS;


#define DMX_READ_OR_RETURN_ERROR(var, expr) \
    const auto var = (expr);                      \
    do {                                          \
        if (DMXReader::has_read_error()) {        \
            return DMXReader::get_read_error();   \
        }                                         \
    } while (0)


class DMXMessage {
private:
    static const DMXResultCode processing_message_standard() {
        uint8_t package_size = MessageMetadata::get_message_size();
        if ((MessageMetadata::get_size() % package_size) != 0 || MessageMetadata::get_size() / package_size > 512) {
            return DMXResultCode::UNCORRECT_MSG_SIZE;
        }
        while (DMXReader::bytes_remaining()) {
            DMX_READ_OR_RETURN_ERROR(address, DMXReader::read_address());
            DMX_READ_OR_RETURN_ERROR(value, DMXReader::read_value());
            DmxSimple.write(address, value);
        }

        return DMXResultCode::SUCCESS;
    }

    static const DMXResultCode processing_message_address_compress() {
        while (DMXReader::bytes_remaining()) {
            DMX_READ_OR_RETURN_ERROR(count, DMXReader::read_count());
            DMX_READ_OR_RETURN_ERROR(start_address, DMXReader::read_address());
            if (count > DMXModule::DMX_MAX_CHANNEL || 
                start_address > DMXModule::DMX_MAX_CHANNEL - count + 1) {
                return DMXResultCode::UNCORRECT_ADDRESS;
            }
            for (uint16_t i = 0; i < count; i++) {
                const uint16_t address = start_address + i;
                DMX_READ_OR_RETURN_ERROR(value, DMXReader::read_value());
                DmxSimple.write(address, value);
            }
        }

        return DMXResultCode::SUCCESS;
    }

    static const DMXResultCode processing_message_address_values_compress() {
        while (DMXReader::bytes_remaining()) {
            DMX_READ_OR_RETURN_ERROR(address_length, DMXReader::read_address_length());
            DMX_READ_OR_RETURN_ERROR(start_address, DMXReader::read_address());
            if (start_address + address_length - 1 > DMXModule::DMX_MAX_CHANNEL) {
                return DMXResultCode::UNCORRECT_ADDRESS;
            }
            uint16_t address = start_address;
            uint16_t total_covered = 0;
            while (address < start_address + address_length) {
                DMX_READ_OR_RETURN_ERROR(count, DMXReader::read_count());
                DMX_READ_OR_RETURN_ERROR(value, DMXReader::read_value());
                uint16_t remaining = (start_address + address_length) - address;
                if (count > remaining) {
                    return DMXResultCode::UNCORRECT_MSG_SIZE;
                }
                for (uint16_t n = 0; n < count; n++) {
                    if (!DMXModule::check_address(address)) {
                        return DMXResultCode::UNCORRECT_ADDRESS;
                    }
                    DmxSimple.write(address, value);
                    address += 1;
                }
                total_covered += count;
            }
            if (total_covered != address_length) {
                return DMXResultCode::UNCORRECT_MSG_SIZE;
            }
        }

        return DMXResultCode::SUCCESS;
    }

    static const DMXResultCode processing_message_type() {
        DMXResultCode result;
        if (MessageMetadata::is_message_type_terminate()) {
            Connection::set_mode_waiting();
            result = DMXResultCode::TERMINATE_CONNECTION;
        }
        else if (MessageMetadata::get_size() == 0 || MessageMetadata::get_size() > DMXModule::DMX_MAX_MSG_SIZE) {
            result = DMXResultCode::UNCORRECT_MSG_SIZE;
        }
        else if (MessageMetadata::is_message_type_standard()) {
            result = processing_message_standard();
        }
        else if (MessageMetadata::is_message_type_address_compress()) {
            result = processing_message_address_compress();
        }
        else if (MessageMetadata::is_message_type_address_values_compress()) {
            result = processing_message_address_values_compress();
        }
        else {
            result = DMXResultCode::UNCORRECT_MSG_TYPE;
        }

        if ((result == DMXResultCode::SUCCESS) && (!DMXReader::check_bytes_readed_success())) {
            result = DMXResultCode::UNCORRECT_MSG_SIZE;
        }
        return result;
    }
public:
    static const uint8_t processing_message() {
        DMXReader::reset();
        MessageMetadata::ReadMetadataResult read_metadata_result = MessageMetadata::read_from_serial();

        if (read_metadata_result == MessageMetadata::ReadMetadataResult::CRC_ERROR) {
            SerialUtils::clear_buffer();
            return static_cast<uint8_t>(DMXResultCode::CRC_ERROR);
        }
        else if (read_metadata_result == MessageMetadata::ReadMetadataResult::READ_ERROR) {
            SerialUtils::clear_buffer();
            return static_cast<uint8_t>(DMXResultCode::READ_ERROR);
        }

        const DMXResultCode result_code = processing_message_type();
        if (result_code != DMXResultCode::SUCCESS && result_code != DMXResultCode::TERMINATE_CONNECTION) {
            SerialUtils::clear_buffer();
        }

        return static_cast<uint8_t>(result_code);
    }

    static void write_watchdog_error() {
        SerialUtils::write_uint8(static_cast<uint8_t>(DMXResultCode::WATCHDOG_ERROR));
    }
};


// ############################################################################
// ############################################################################
// ###############################---SERIAL---#################################
// ############################################################################
// ############################################################################


#define SERIAL_BAUDRATE 115200
#define SERIAL_TIMEOUT 10

class SerialModule {
private:
    static const uint32_t PACKET_TIMEOUT_MS = 10000;
    static uint32_t last_packet_time;

    static inline void check_packet_timeout() {
        if ((uint32_t)(millis() - last_packet_time) > PACKET_TIMEOUT_MS) {
            SerialUtils::write_uint8(static_cast<uint8_t>(DMXResultCode::TERMINATE_CONNECTION));
            Connection::set_mode_waiting();
            SerialUtils::clear_buffer();
        }
    }
public:
    static inline void update_last_packet_time() {
        last_packet_time = millis();
    }

    static inline void init() {
        Serial.begin(SERIAL_BAUDRATE);
        Serial.setTimeout(SERIAL_TIMEOUT);
        while(!Serial);
    }

    static inline void loop() {
        if (MessageMetadata::available()) {
            update_last_packet_time();
            const uint8_t result_code = DMXMessage::processing_message();
            SerialUtils::write_uint8(result_code);
        }
        else {
            check_packet_timeout();
        }
    }
};
static uint32_t SerialModule::last_packet_time = 0;
void reset_serial_packet_timeout() {
    SerialModule::update_last_packet_time();
}

// ############################################################################
// ############################################################################
// ################################---MAIN---##################################
// ############################################################################
// ############################################################################


ISR(WDT_vect) {
    // Force reset: переключаем в reset mode с ~16 мс
    cli();  // Отключаем прерывания на setup WDT
    wdt_reset();  // Clear current
    WDTCSR |= (1 << WDCE) | (1 << WDE);  // Change enable: unlock + set WDE=1
    WDTCSR = (1 << WDE) | (1 << WDP0);   // Reset mode, shortest timeout (~16 ms)
    // Вообще, как будто бы хуево так делать - в обработчике прерывания писать
    // в serial. Но что мне еще остается? Да и прерывания я отключил.
    // if (Connection::if_mode_serial() && (Serial.availableForWrite() > 0)) {
    //     DMXMessage::write_watchdog_error();
    // }
    // Оказывается, программный сброс не разрывает соединение. Вероятно.
    // WDRF флаг установится автоматически
    while (1);
}

void setup() {
    DMXModule::init();
    SerialModule::init();
    if (MCUSR & (1 << WDRF)) {  // последняя работа завершилась программным сбросом
        DMXMessage::write_watchdog_error();
        MCUSR &= ~(1 << WDRF);   // очистить флаг
        Connection::set_mode_serial();
    }
    else {
        // Зачем?
        // Connection::write_handshake_msg();
    }

    cli();  // Отключаем прерывания
    wdt_reset();
    wdt_disable();  // Полностью отключаем WDT перед настройкой
    WDTCSR |= (1 << WDCE) | (1 << WDE);  // Unlock для изменений
    WDTCSR = (1 << WDIE) | (1 << WDP2);  // ~250 мс, interrupt only
    sei();  // Включаем прерывания
}

const unsigned int MAIN_LOOP_SLEEP_TIME_MCS = 200;
void loop() {
    wdt_reset();
    if (Connection::if_mode_waiting()) {
        Connection::check_serial_connection();
    }
    else if (Connection::if_mode_serial()) {
        SerialModule::loop();
    }
    delayMicroseconds(MAIN_LOOP_SLEEP_TIME_MCS);
}
