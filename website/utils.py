import struct
import struct

def get_image_size(stream):
    """Returns (width, height) for a given file-like object stream."""

    data = stream.read(25)
    if data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        # PNG images
        if data[12:16] == b'IHDR':
            w, h = struct.unpack('>LL', data[16:24])
        else:
            # older PNGs
            w, h = struct.unpack('>LL', data[8:16])
        return int(w), int(h)
    elif data.startswith(b'\xFF\xD8'):
        # JPEG images
        stream.seek(0)
        stream.read(2)
        byte = stream.read(1)
        while byte and byte != b'\xDA':
            while byte != b'\xFF': byte = stream.read(1)
            while byte == b'\xFF': byte = stream.read(1)

            if 0xC3 >= ord(byte) >= 0xC0:
                stream.read(3)
                h, w = struct.unpack('>HH', stream.read(4))
                return int(w), int(h)
            else:
                to_read = struct.unpack('>H', stream.read(2))
                stream.read(to_read[0] - 2)
            byte = stream.read(1)
    else:
        raise Exception('Unsupported image type')
