class ApiException(BaseException):
    def __init__(self, *args, response_json: dict=None):
        super(ApiException, self).__init__(*args)
        self.response_json = response_json
