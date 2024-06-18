import enum


class Command(bytes, enum.Enum):
    SET_CIPHER_MODE_ECB = (b"\x00",)
    SET_CIPHER_MODE_CBC = (b"\x01",)
    SET_CIPHER_MODE_CTR = (b"\x02",)
    SET_KEY_128 = (b"\x12",)
    SET_KEY_192 = (b"\x13",)
    SET_KEY_256 = (b"\x14",)
    SET_IV = (b"\x15",)
    SET_INPUT = (b"\x10",)
    ENCRYPT_INPUT = b"\x30"
    ENCRYPT_LAST_OUTPUT = b"\x31"
    DECRYPT_INPUT = b"\x40"
    DECRYPT_LAST_OUTPUT = b"\x41"
    GET_INPUT = (b"\x20",)
    GET_OUTPUT = b"\x21"
    GET_KEY_128 = (b"\x22",)
    GET_KEY_192 = (b"\x23",)
    GET_KEY_256 = (b"\x24",)
    GET_KEY_LENGTH = b"\x25"
    GET_IV = (b"\x26",)
    GET_CIPHER_MODE = b"\x27"
    GET_INFO = (b"\x28",)


class CipherMode(enum.IntEnum):
    ECB = (0,)
    CBC = (1,)
    CTR = 2


class TargetCommunication(object):
    def __init__(self, serial):
        """
        Hand over serial object
        :param serial:
        """
        self._serial = serial

    def __del__(self):
        try:
            self._serial.close()
        except AttributeError:
            return

    def set_input(self, inp):
        self._serial.write(Command.SET_INPUT + bytes(inp))

    def get_input(self):
        self._serial.write(Command.GET_INPUT)
        return self._serial.read(16)

    def set_iv(self, iv):
        self._serial.write(Command.SET_IV + bytes(iv))

    def get_iv(self):
        self._serial.write(Command.GET_IV)
        return self._serial.read(16)

    def set_cipher_mode(self, mode):
        if mode not in CipherMode:
            raise ValueError("Invalid cipher mode")

        if mode == CipherMode.ECB:
            self._serial.write(Command.SET_CIPHER_MODE_ECB)
        elif mode == CipherMode.CBC:
            self._serial.write(Command.SET_CIPHER_MODE_CBC)
        elif mode == CipherMode.CTR:
            self._serial.write(Command.SET_CIPHER_MODE_CTR)

    def get_cipher_mode(self):
        self._serial.write(Command.GET_CIPHER_MODE)
        return CipherMode(self._serial.read(1)[0])

    def encrypt_input(self):
        self._serial.write(Command.ENCRYPT_INPUT)
        return self._serial.read(16)

    def encrypt_last_output(self):
        self._serial.write(Command.ENCRYPT_LAST_OUTPUT)
        return self._serial.read(16)

    def decrypt_input(self):
        self._serial.write(Command.DECRYPT_INPUT)
        return self._serial.read(16)

    def decrypt_last_output(self):
        self._serial.write(Command.DECRYPT_LAST_OUTPUT)
        return self._serial.read(16)

    def get_output(self):
        self._serial.write(Command.GET_OUTPUT)
        return self._serial.read(16)

    def get_key_128(self):
        self._serial.write(Command.GET_KEY_128)
        return self._serial.read(16)

    def get_key_192(self):
        self._serial.write(Command.GET_KEY_192)
        return self._serial.read(24)

    def get_key_256(self):
        self._serial.write(Command.GET_KEY_256)
        return self._serial.read(32)

    def set_key_128(self, key):
        self._serial.write(Command.SET_KEY_128 + key)

    def set_key_192(self, key):
        self._serial.write(Command.SET_KEY_192 + key)

    def set_key_256(self, key):
        self._serial.write(Command.SET_KEY_256 + key)

    def get_key_length(self):
        self._serial.write(Command.GET_KEY_LENGTH)
        return self._serial.read(1)[0]

    def get_info(self):
        self._serial.write(Command.GET_INFO)
        return self._serial.read(20)
