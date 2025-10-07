from escpos.printer import Usb
from PIL import Image

try: 
    p=Usb(0x0416, 0x5011, in_ep=0x81, out_ep=0x03)

    img = Image.open("ipfs_qrcode.png")
    img = img.resize((400, 400))

    p.image(img)
    p.cut()
    p.close()

except Exception as e:
    print(f"Error: Thermal printer not connected or accessible - {e}")


