def apply_patch():
    from kivy.lang import Builder

    Builder.load_string("""
<-RelativeLayout>:
    canvas.before:
        PushMatrix
        Translate:
            xy: (round(self.x), round(self.y))
    canvas.after:
        PopMatrix
    """
    )
