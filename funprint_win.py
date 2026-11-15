import asyncio
import threading
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageOps, ImageTk, ImageEnhance, ImageDraw, ImageFont
from bleak import BleakScanner, BleakClient

CRC = [0x00,0x07,0x0e,0x09,0x1c,0x1b,0x12,0x15,0x38,0x3f,0x36,0x31,0x24,0x23,0x2a,0x2d,0x70,0x77,0x7e,0x79,0x6c,0x6b,0x62,0x65,0x48,0x4f,0x46,0x41,0x54,0x53,0x5a,0x5d,0xe0,0xe7,0xee,0xe9,0xfc,0xfb,0xf2,0xf5,0xd8,0xdf,0xd6,0xd1,0xc4,0xc3,0xca,0xcd,0x90,0x97,0x9e,0x99,0x8c,0x8b,0x82,0x85,0xa8,0xaf,0xa6,0xa1,0xb4,0xb3,0xba,0xbd,0xc7,0xc0,0xc9,0xce,0xdb,0xdc,0xd5,0xd2,0xff,0xf8,0xf1,0xf6,0xe3,0xe4,0xed,0xea,0xb7,0xb0,0xb9,0xbe,0xab,0xac,0xa5,0xa2,0x8f,0x88,0x81,0x86,0x93,0x94,0x9d,0x9a,0x27,0x20,0x29,0x2e,0x3b,0x3c,0x35,0x32,0x1f,0x18,0x11,0x16,0x03,0x04,0x0d,0x0a,0x57,0x50,0x59,0x5e,0x4b,0x4c,0x45,0x42,0x6f,0x68,0x61,0x66,0x73,0x74,0x7d,0x7a,0x89,0x8e,0x87,0x80,0x95,0x92,0x9b,0x9c,0xb1,0xb6,0xbf,0xb8,0xad,0xaa,0xa3,0xa4,0xf9,0xfe,0xf7,0xf0,0xe5,0xe2,0xeb,0xec,0xc1,0xc6,0xcf,0xc8,0xdd,0xda,0xd3,0xd4,0x69,0x6e,0x67,0x60,0x75,0x72,0x7b,0x7c,0x51,0x56,0x5f,0x58,0x4d,0x4a,0x43,0x44,0x19,0x1e,0x17,0x10,0x05,0x02,0x0b,0x0c,0x21,0x26,0x2f,0x28,0x3d,0x3a,0x33,0x34,0x4e,0x49,0x40,0x47,0x52,0x55,0x5c,0x5b,0x76,0x71,0x78,0x7f,0x6a,0x6d,0x64,0x63,0x3e,0x39,0x30,0x37,0x22,0x25,0x2c,0x2b,0x06,0x01,0x08,0x0f,0x1a,0x1d,0x14,0x13,0xae,0xa9,0xa0,0xa7,0xb2,0xb5,0xbc,0xbb,0x96,0x91,0x98,0x9f,0x8a,0x8d,0x84,0x83,0xde,0xd9,0xd0,0xd7,0xc2,0xc5,0xcc,0xcb,0xe6,0xe1,0xe8,0xef,0xfa,0xfd,0xf4,0xf3]
CHAR_UUID = "0000ae01-0000-1000-8000-00805f9b34fb"

def pkt(cmd, d):
    c = 0
    for b in d: c = CRC[(c ^ b) & 0xff]
    return bytes([0x51, 0x78, cmd, 0x00, len(d) & 0xff, (len(d) >> 8) & 0xff]) + d + bytes([c, 0xff])

def prep_img(im, contraste):
    im = im.convert("L")
    im = im.resize((384, max(1, int(im.height * 384 / im.width))), Image.Resampling.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(contraste)
    return ImageOps.invert(im).convert("1")

async def enviar_ble(im, nivel_calor, pausa_ms, st):
    st("Buscando impresora MX06 / termica...")
    devices = await BleakScanner.discover(timeout=5.0)
    target = None
    for d in devices:
        nombre = (d.name or "").upper()
        if any(k in nombre for k in ["MX0", "GB0", "GT0", "YT0", "FUN", "MINI"]):
            target = d
            break
    if not target:
        st("Error: No se encontro la impresora. Enciendela y activa Bluetooth.")
        return

    st(f"Conectando a {target.name}...")
    async with BleakClient(target.address) as client:
        await asyncio.sleep(0.5)

        async def escribir(datos):
            for i in range(0, len(datos), 20):
                await client.write_gatt_char(CHAR_UUID, datos[i:i+20], response=False)
                await asyncio.sleep(0.005)

        energia = min(255, int(48 + (nivel_calor * 20)))
        st(f"Calentando cabezal (Nivel {nivel_calor}/10)...")
        await escribir(pkt(0xAF, bytes([energia, 0x00])))
        await asyncio.sleep(0.05)
        await escribir(pkt(0xBD, bytes([0x14])))
        await escribir(pkt(0xBE, bytes([0x00])))
        await asyncio.sleep(0.1)

        px = list(im.getdata())
        for y in range(im.height):
            fb = bytearray(48)
            for bi in range(48):
                b = 0
                for bit in range(8):
                    if px[y*384 + bi*8 + bit] > 0: b |= (1 << bit)
                fb[bi] = b
            await escribir(pkt(0xA2, bytes(fb)))
            if pausa_ms > 0:
                await asyncio.sleep(pausa_ms / 1000.0)
            if y % 12 == 0:
                pct = int((y / max(1, im.height)) * 100)
                st(f"Imprimiendo... {pct}% ({y}/{im.height})")

        await asyncio.sleep(0.2)
        await escribir(pkt(0xA1, bytes([0x55, 0x00])))
        st("Impresion completada al 100%!")

img_base = None
def elegir():
    global img_base
    r = filedialog.askopenfilename(filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.bmp *.webp")])
    if not r: return
    img_base = Image.open(r)
    actualizar_preview()
    btn_p.config(state="normal")

def usar_texto():
    global img_base
    txt = entry_txt.get().strip()
    if not txt: return
    im = Image.new("L", (384, 100), 255)
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
    draw.text((15, 25), txt, fill=0, font=font)
    img_base = im
    actualizar_preview()
    btn_p.config(state="normal")

def actualizar_preview(*args):
    if img_base is None: return
    im = prep_img(img_base, slider_cont.get())
    pv = ImageOps.invert(im.convert("L"))
    if pv.height > 200: pv = pv.resize((int(pv.width * 200 / pv.height), 200))
    tk_im = ImageTk.PhotoImage(pv)
    lpv.config(image=tk_im, text="")
    lpv.image = tk_im

def run_p():
    if img_base is None: return
    btn_p.config(state="disabled")
    im = prep_img(img_base, slider_cont.get())
    calor, pausa = slider_calor.get(), slider_pausa.get()
    def t():
        try:
            asyncio.run(enviar_ble(im, calor, pausa, lambda x: root.after(0, lambda: lst.config(text=x))))
        except Exception as e:
            root.after(0, lambda: lst.config(text=f"Error: {e}"))
        root.after(0, lambda: btn_p.config(state="normal"))
    threading.Thread(target=t, daemon=True).start()

root = tk.Tk(); root.title("FunPrint Windows v2.1 (Open Source)"); root.geometry("480x660"); root.configure(bg="#1e1e1e")
tk.Label(root, text="FunPrint Windows v2.1", bg="#1e1e1e", fg="#38bdf8", font=("Segoe UI", 14, "bold")).pack(pady=8)
tk.Button(root, text="1. Elegir imagen del PC", command=elegir, bg="#2d2d2d", fg="#fff", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=6).pack(pady=4)

entry_txt = tk.Entry(root, bg="#2d2d2d", fg="#fff", insertbackground="#fff", font=("Segoe UI", 11), width=30)
entry_txt.pack(pady=4)
tk.Button(root, text="Usar texto escrito arriba", command=usar_texto, bg="#2563eb", fg="#fff", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=4).pack(pady=2)

f_ctrl = tk.Frame(root, bg="#252525", padx=12, pady=8); f_ctrl.pack(fill="x", padx=20, pady=6)
tk.Label(f_ctrl, text="Temperatura / Energia Cabezal (1 - 10):", bg="#252525", fg="#fb923c", font=("Segoe UI", 9, "bold")).pack(anchor="w")
slider_calor = tk.Scale(f_ctrl, from_=1, to=10, orient="horizontal", bg="#252525", fg="#fff", highlightthickness=0); slider_calor.set(8); slider_calor.pack(fill="x")

tk.Label(f_ctrl, text="Contraste de imagen (1.0 - 3.0):", bg="#252525", fg="#38bdf8", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6,0))
slider_cont = tk.Scale(f_ctrl, from_=1.0, to=3.0, resolution=0.2, orient="horizontal", bg="#252525", fg="#fff", highlightthickness=0, command=actualizar_preview); slider_cont.set(1.8); slider_cont.pack(fill="x")

tk.Label(f_ctrl, text="Pausa entre lineas (ms):", bg="#252525", fg="#a3e635", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6,0))
slider_pausa = tk.Scale(f_ctrl, from_=0, to=40, orient="horizontal", bg="#252525", fg="#fff", highlightthickness=0); slider_pausa.set(15); slider_pausa.pack(fill="x")

lpv = tk.Label(root, text="Vista previa (384px)", bg="#141414", fg="#777", width=45, height=10); lpv.pack(pady=6, padx=20)
btn_p = tk.Button(root, text="2. IMPRIMIR POR BLUETOOTH", command=run_p, state="disabled", bg="#22c55e", fg="#000", font=("Segoe UI", 11, "bold"), relief="flat", padx=15, pady=8); btn_p.pack(pady=4)
lst = tk.Label(root, text="Enciende la impresora y activa Bluetooth + Ubicacion", bg="#1e1e1e", fg="#fbbf24", font=("Segoe UI", 9)); lst.pack(pady=6)
root.mainloop()
