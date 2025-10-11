# from escpos.printer import Usb
# from PIL import Image

# try: 
#     p=Usb(0x0416, 0x5011, in_ep=0x81, out_ep=0x03)

#     img = Image.open("ipfs_qrcode.png")
#     img = img.resize((400, 400))

#     p.image(img)
#     p.cut()
#     p.close()

# except Exception as e:
#     print(f"Error: Thermal printer not connected or accessible - {e}")





from escpos.printer import Usb
from PIL import Image

# List of endpoint configurations to try
endpoint_configs = [
    {'in_ep': 0x81, 'out_ep': 0x01},
    {'in_ep': 0x81, 'out_ep': 0x03}
]

success = False

for config in endpoint_configs:
    try:
        print(f"Trying endpoints: in_ep={hex(config['in_ep'])}, out_ep={hex(config['out_ep'])}")
        
        p = Usb(0x0416, 0x5011, **config)
        
        img = Image.open("ipfs_qrcode.png")
        img = img.resize((400, 400))
        
        p.image(img)
        p.cut()
        p.close()
        
        print(f"✓ Print successful with out_ep={hex(config['out_ep'])}")
        success = True
        break
        
    except Exception as e:
        print(f"✗ Failed with out_ep={hex(config['out_ep'])}: {e}")
        continue

from escpos.printer import Usb
from PIL import Image

# List of endpoint configurations to try
endpoint_configs = [
    {'in_ep': 0x81, 'out_ep': 0x01},
    {'in_ep': 0x81, 'out_ep': 0x03}
]

success = False

for config in endpoint_configs:
    try:
        print(f"Trying endpoints: in_ep={hex(config['in_ep'])}, out_ep={hex(config['out_ep'])}")
        
        p = Usb(0x0416, 0x5011, **config)
        
        img = Image.open("ipfs_qrcode.png")
        img = img.resize((400, 400))
        
        p.image(img)
        p.cut()
        p.close()
        
        print(f"✓ Print successful with out_ep={hex(config['out_ep'])}")
        success = True
        break
        
    except Exception as e:
        print(f"✗ Failed with out_ep={hex(config['out_ep'])}: {e}")
        continue

if not success:
    print("\nAll endpoint configurations failed.")
    print("Try running: lsusb -v -d 0416:5011 | grep bEndpointAddress")