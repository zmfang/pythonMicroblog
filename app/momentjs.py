from jinja2 import Markup
# from .views import g


# 封装一个简单的python类
class momentsjs(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def render(self, format):
        return Markup("<script>\ndocument.write(moment(\"%s\").%s);\n</script>") % (self.timestamp.strftime("%Y-%m-%dT%H:%M:%S Z"), format)

    def format(self, fmt):
        return self.render(Markup("format(\"%s\")" % fmt))

    def calendar(self):
        return self.render("calendar()")

    def fromNow(self):
        return self.render("fromNow()")
