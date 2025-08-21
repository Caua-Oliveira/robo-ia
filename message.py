class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def full_message(self):
        return {"role": self.role, "content": self.content}

    def __str__(self):
        return f"{self.__class__.__name__}: {', '.join([f'{key}={value}' for key, value in self.__dict__.items()])}"
