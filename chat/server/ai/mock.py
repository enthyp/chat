class Checker:
    keywords = ['honkey', 'honkie']

    @classmethod
    def check(cls, msg):
        return any([kw in msg for kw in cls.keywords])