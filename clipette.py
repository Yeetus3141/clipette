import ctypes
from ctypes.wintypes import *

GMEM_MOVABLE = 2
CF_UNICODETEXT = 13
CF_BITMAP = 2   # hbitmap
CF_DIB = 8   # DIB and BITMAP are interconvertable as from windows clipboard
CF_DIBV5 = 17

# bitmap compression types
BI_RGB = 0
BI_RLE8 = 1
BI_RLE4 = 2
BI_BITFIELDS = 3
BI_JPEG = 4
BI_PNG = 5
BI_ALPHABITFIELDS = 6

format_dict = {
    'CF_BITMAP': 2,
    'CF_DIB': 8,
    'CF_DIBV5': 17,
    'CF_DIF': 5,
    'CF_ENHMETAFILE': 14,
    'CF_OEMTEXT': 7,
    'CF_PALETTE': 9,
    'CF_PENDATA': 10,
    'CF_TEXT': 1,
    'CF_UNICODETEXT': 13,
    }

# todo:
# implement more formats (DIBV5, JPEG, PNG) in get_DIB
# implement transparency in set_DIB

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

open_cb = user32.OpenClipboard
open_cb.argtypes = HWND,
open_cb.restype = BOOL
get_cb = user32.GetClipboardData
get_cb.argtypes = UINT,
get_cb.restype = HANDLE
set_cb = user32.SetClipboardData
set_cb.argtypes = UINT, HANDLE
set_cb.restype = HANDLE
global_lock = kernel32.GlobalLock
global_lock.argtypes = HGLOBAL, 
global_lock.restypes = LPCVOID
global_unlock = kernel32.GlobalUnlock
global_unlock.argtypes = HGLOBAL,
global_unlock.restype = BOOL
close_cb = user32.CloseClipboard
close_cb.argtypes = None
close_cb.restype = BOOL


class BITMAPFILEHEADER(ctypes.Structure):
    _pack_ = 1  # structure field byte alignment
    _fields_ = [
        ('bfType', WORD),  # file type ("BM")
        ('bfSize', DWORD),  # file size in bytes
        ('bfReserved1', WORD),  # must be zero
        ('bfReserved2', WORD),  # must be zero
        ('bfOffBits', DWORD),  # byte offset to the pixel array
    ]   
sizeof_BITMAPFILEHEADER = ctypes.sizeof(BITMAPFILEHEADER)

class BITMAPINFOHEADER(ctypes.Structure):
    _pack_ = 1  # structure field byte alignment
    _fields_ = [
        ('biSize', DWORD),
        ('biWidth', LONG),
        ('biHeight', LONG),
        ('biPLanes', WORD),
        ('biBitCount', WORD),
        ('biCompression', DWORD),
        ('biSizeImage', DWORD),
        ('biXPelsPerMeter', LONG),
        ('biYPelsPerMeter', LONG),
        ('biClrUsed', DWORD),
        ('biClrImportant', DWORD)
    ]
sizeof_BITMAPINFOHEADER = ctypes.sizeof(BITMAPINFOHEADER)

class BITMAPV4HEADER(ctypes.Structure):
    _pack_ = 1 # structure field byte alignment
    _fields_ = [
        ('bV4Size', DWORD),
        ('bV4Width', LONG),
        ('bV4Height', LONG),
        ('bV4PLanes', WORD),
        ('bV4BitCount', WORD),
        ('bV4Compression', DWORD),
        ('bV4SizeImage', DWORD),
        ('bV4XPelsPerMeter', LONG),
        ('bV4YPelsPerMeter', LONG),
        ('bV4ClrUsed', DWORD),
        ('bV4ClrImportant', DWORD),
        ('bV4RedMask', DWORD),
        ('bV4GreenMask', DWORD),
        ('bV4BlueMask', DWORD),
        ('bV4AlphaMask', DWORD),
        ('bV4CSMask', DWORD),
        ('bV4RedEndpointX', LONG),
        ('bV4RedEndpointY', LONG),
        ('bV4RedEndpointZ', LONG),
        ('bV4GreenEndpointX', LONG),
        ('bV4GreenEndpointY', LONG),
        ('bV4GreenEndpointZ', LONG),
        ('bV4BlueEndpointX', LONG),
        ('bV4BlueEndpointY', LONG),
        ('bV4BlueEndpointZ', LONG),
        ('bV4GammaRed', DWORD),
        ('bV4GammaGreen', DWORD),
        ('bV4GammaBlue', DWORD)
    ]
sizeof_BITMAPV4HEADER = ctypes.sizeof(BITMAPV4HEADER)

def BITMAPINFO_to_BITMAPV4(bmp_info):
    """
    converts bitmap with older BITMAPINFOHEADER to BITMAPV4HEADER (which truly supports an alpha channel).

    :param bytes bmp_info: source bitmap data. Must be of BITMAPINFOHEADER format starting from the header structure.
    """

    # BITMAPINFOHEADER _technically_ does not support an alpha channel, but has an 'extra' channel which some softwares treat as alpha.
    # So we need to convert a BITMAPINFOHEADER to BITMAPV4HEADER (which does support alpha) for other softwares to recognize the alpha channel
    # This function fills in the extra header space with default values.
    # info on these header structures -> https://docs.microsoft.com/en-us/windows/win32/gdi/bitmap-header-types
    # and -> https://en.wikipedia.org/wiki/BMP_file_format

    if (bmp_info[0] != 40):
        raise ValueError('source bitmap is not in the expected format')
        return 0

    bi_size = bytes([108, 0, 0, 0])
    bi_bitmasks = bytes([0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0, 0, 0, 0, 0, 255])
    bi_extra = bytearray(52)

    bmp_v4 = bi_size + bmp_info[4:40] + bi_bitmasks + bi_extra + bmp_info[40:]
    return bmp_v4

def get_UNICODETEXT():
    """
    get text from clipboard as string 

    :return: (str) text grabbed from clipboard 
    """

    user32.OpenClipboard(0)
    data = user32.GetClipboardData(CF_UNICODETEXT)
    dest = kernel32.GlobalLock(data)
    text = ctypes.wstring_at(dest)
    kernel32.GlobalUnlock(data)
    user32.CloseClipboard()

    return text

def set_UNICODETEXT(text):
    """
    set text to clipboard as CF_UNICODETEXT 

    :param str text: text to set to clipboard
    """

    data = text.encode('utf-16le')
    size = len(data) + 2

    h_mem = kernel32.GlobalAlloc(GMEM_MOVABLE, size)
    dest = kernel32.GlobalLock(h_mem)
    ctypes.memmove(dest, data, size)
    kernel32.GlobalUnlock(h_mem)

    user32.OpenClipboard(0)
    user32.SetClipboardData(CF_UNICODETEXT, h_mem)
    user32.CloseClipboard()

def get_DIB(filepath = 'bitmap.bmp', as_bmpV4 = False):
    """
    get image from clipboard as a bitmap 

    :param str filepath: filepath (path/bitmap.bmp) to save image into 
    :param bool as_bmpV4: whether to pull image as a bitmapV4 (with supported alpha channel)
    """

    user32.OpenClipboard(0)

    h_mem = user32.GetClipboardData(CF_DIB)
    dest = kernel32.GlobalLock(h_mem)
    size = kernel32.GlobalSize(dest)
    print('size ', size)
    
    data = bytes((ctypes.c_char*size).from_address(dest))

    if data[0] == 40:
        if as_bmpV4:
            bm_ih = BITMAPV4HEADER()
            header_size = sizeof_BITMAPV4HEADER
            data = BITMAPINFO_to_BITMAPV4(data)
            ctypes.memmove(ctypes.pointer(bm_ih), data, header_size)

            if bm_ih.bV4Compression != BI_BITFIELDS: 
                print(f'unsupported compression type {format(bm_ih.biCompression)}')
                return 0
        else:
            bm_ih = BITMAPINFOHEADER()
            header_size = sizeof_BITMAPINFOHEADER
            ctypes.memmove(ctypes.pointer(bm_ih), data, header_size)

            if bm_ih.biCompression != BI_BITFIELDS: 
                print(f'unsupported compression type {format(bm_ih.biCompression)}')
                return 0         
    else:
        print('unsupported image format on clipboard')
        return 0

    bm_fh = BITMAPFILEHEADER()
    ctypes.memset(ctypes.pointer(bm_fh), 0, sizeof_BITMAPFILEHEADER)
    bm_fh.bfType = ord('B') | (ord('M') << 8)
    bm_fh.bfSize = sizeof_BITMAPFILEHEADER + len(str(data))
    sizeof_COLORTABLE = 0
    bm_fh.bfOffBits = sizeof_BITMAPFILEHEADER + header_size + sizeof_COLORTABLE

    with open(filepath, 'wb') as bmp_file:
        bmp_file.write(bm_fh)
        bmp_file.write(data)

    kernel32.GlobalUnlock(h_mem)
    user32.CloseClipboard()

def set_DIB(src_bmp):
    """
    set source bitmap image to clipboard as a CF_DIB 

    :param str src_bmp: File path of source image
    """

    with open(src_bmp, 'rb') as img:
        data = img.read()
    output = data[14:]
    size = len(output)

    mem = kernel32.GlobalAlloc(GMEM_MOVABLE, size)
    h_mem = kernel32.GlobalLock(mem)
    ctypes.memmove(h_mem, output, size) 
    kernel32.GlobalUnlock(mem)

    user32.OpenClipboard(0)
    user32.SetClipboardData(CF_DIB, h_mem)
    user32.CloseClipboard()
    
def is_format_available(format_id):
    """
    checks whether specified format is currently available on the clipboard

    :param int format_id: id of format to check for
    :return: (bool) True if specified format is available
    """
    
    user32.OpenClipboard(0)
    is_format = user32.IsClipboardFormatAvailable(format_id)
    user32.CloseClipboard()
    return bool(is_format)

# prints available formats
# for format in format_dict:
#     if is_format_available(format_dict[format]):
#         print('format available: ', format)

if __name__ == '__main__':
    set_UNICODETEXT('pasta pasta')
    # get_DIB(as_bmpV4=True)

    # with open('test_bmp4.bmp', 'rb') as img:
    #     d = img.read()
    # print(list(d[14:]))
    # print(len(d))
