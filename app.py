from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageFilter, ImageOps, ImageTk

from enhance import enhance, load_photo, save_photo
from updates import VERSION, download_and_launch, get_asset

INK = "#112b53"
MUTED = "#4c6380"
BLUE = "#145bd9"
WHITE = "#ffffff"
ICE = "#eef6ff"
ASSETS = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))


class App:
    def __init__(self, root):
        self.root = root
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.source = self.result = self.path = None
        self.preview = None
        self.preview_key = None
        self.layers = None
        self.busy = False
        self.split = tk.IntVar(value=48)
        self.scale = tk.StringVar(value="2×")
        self.denoise = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Abra uma foto para começar.")
        self.dimensions = tk.StringVar(value="JPG, PNG, WebP, BMP ou TIFF")
        root.title("Fotos Aprimoradas · Lab Gusto")
        root.geometry("1120x720")
        root.minsize(860, 620)
        root.configure(bg=ICE)
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TCombobox", padding=7)
        style.configure("TScale", background=WHITE, troughcolor="#e2efff")
        style.configure("TCheckbutton", background=WHITE, foreground=INK, font=("Segoe UI", 10))
        mark = tk.Frame(root, bg=ICE)
        mark.pack(fill="x", padx=32, pady=(22, 14))
        self.label(mark, "lab.gusto  /  IMAGEM", 10, BLUE, ICE, True).pack(anchor="w")
        self.label(mark, "Fotos Aprimoradas", 29, INK, ICE, True).pack(anchor="w")
        self.label(mark, "Amplie, ajuste a nitidez e compare o resultado.", 11, MUTED, ICE).pack(anchor="w")
        main = tk.Frame(root, bg=ICE)
        main.pack(fill="both", expand=True, padx=32)
        panel = tk.Frame(main, bg=WHITE, padx=20, pady=20, width=260)
        panel.pack(side="right", fill="y", padx=(18, 0))
        panel.pack_propagate(False)
        compare = tk.Frame(main, bg=WHITE, padx=14, pady=12)
        compare.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(compare, bg="#d8eaff", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self.draw())
        self.canvas.bind("<Button-1>", self.move_split)
        self.canvas.bind("<B1-Motion>", self.move_split)
        ttk.Scale(compare, from_=0, to=100, variable=self.split,
                  command=lambda _: self.draw()).pack(fill="x", pady=(10, 2))
        self.caption = self.label(compare, "Demonstração · arraste para comparar", 10, MUTED)
        self.caption.pack(anchor="w")
        self.label(panel, "Sua foto", 17, INK, bold=True).pack(anchor="w")
        self.choose = self.button(panel, "Abrir imagem", self.open_photo)
        self.choose.pack(fill="x", pady=(12, 6))
        tk.Label(panel, textvariable=self.dimensions, wraplength=218, justify="left",
                 bg=WHITE, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 20))
        self.label(panel, "Ampliação", 11, INK, bold=True).pack(anchor="w")
        self.selector = ttk.Combobox(panel, values=("2×", "3×", "4×"), state="readonly",
                                     textvariable=self.scale)
        self.selector.pack(fill="x", pady=(6, 10))
        self.selector.bind("<<ComboboxSelected>>", self.invalidate)
        self.noise = ttk.Checkbutton(panel, text="Redução leve de ruído", variable=self.denoise,
                                     command=self.invalidate)
        self.noise.pack(anchor="w")
        self.run = self.button(panel, "Aprimorar foto", self.process, primary=True)
        self.run.pack(fill="x", pady=(22, 8))
        self.save = self.button(panel, "Salvar resultado", self.export)
        self.save.pack(fill="x")
        self.label(panel, "Processamento no seu computador", 9, MUTED).pack(side="bottom", anchor="w")
        footer = tk.Frame(root, bg=ICE)
        footer.pack(fill="x", padx=32, pady=14)
        tk.Label(footer, textvariable=self.status, bg=ICE, fg=MUTED,
                 font=("Segoe UI", 10), wraplength=620, justify="left").pack(side="left")
        self.update = self.button(footer, "⟳", self.check_updates)
        self.update.configure(width=2, font=("Segoe UI Symbol", 16), padx=6, pady=0)
        self.update.pack(side="right")
        self.update.bind("<Enter>", lambda _: self.update_text.pack(side="right", padx=8))
        self.update.bind("<Leave>", lambda _: self.update_text.pack_forget())
        self.update_text = self.label(footer, "Verificar atualizações", 10, MUTED, ICE)
        self.label(footer, f"v{VERSION}", 9, MUTED, ICE).pack(side="right", padx=10)
        self.demo = self.read_demo()
        self.refresh()

    @staticmethod
    def label(parent, text, size, color, bg=WHITE, bold=False):
        return tk.Label(parent, text=text, fg=color, bg=bg,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    @staticmethod
    def button(parent, text, action, primary=False):
        return tk.Button(parent, text=text, command=action, bg=BLUE if primary else "#e5f0ff",
                         fg=WHITE if primary else INK, activebackground="#b9d8ff",
                         relief="flat", font=("Segoe UI", 10, "bold"), padx=12, pady=9,
                         cursor="hand2", borderwidth=0, highlightthickness=1,
                         highlightcolor=BLUE, highlightbackground=parent.cget("bg"))

    @staticmethod
    def read_demo():
        try:
            image = load_photo(ASSETS / "demo.jpg")
            image.thumbnail((1440, 980))
            return image
        except OSError:
            return None

    def move_split(self, event):
        self.split.set(round(100 * event.x / max(1, self.canvas.winfo_width())))
        self.draw()

    def draw(self):
        canvas = self.canvas
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if min(width, height) < 4:
            return
        canvas.delete("all")
        photo = self.result or self.source or self.demo
        if photo is None:
            canvas.create_text(width / 2, height / 2, text="Abra uma foto para visualizar",
                               fill=INK, font=("Segoe UI", 14))
            return
        key = (photo, width, height)
        if self.preview_key != key:
            after = ImageOps.contain(photo, (width, height), Image.Resampling.LANCZOS)
            if self.source is None:
                before = after.filter(ImageFilter.GaussianBlur(5))
            else:
                before = self.source.resize(after.size, Image.Resampling.LANCZOS)
            self.layers = after, before
            self.preview_key = key
        after, before = self.layers
        after = after.copy()
        x, y = (width - after.width) // 2, (height - after.height) // 2
        cut = max(0, min(after.width, int(width * self.split.get() / 100) - x))
        if cut:
            after.paste(before.crop((0, 0, cut, after.height)), (0, 0))
        self.preview = ImageTk.PhotoImage(after)
        canvas.create_image(x, y, anchor="nw", image=self.preview)
        if self.result is not None or self.source is None:
            bar = x + cut
            canvas.create_line(bar, y, bar, y + after.height, width=3, fill=WHITE)
            middle = height / 2
            canvas.create_oval(bar - 15, middle - 15, bar + 15, middle + 15,
                               fill=WHITE, outline="#b9d8ff", width=1)
            canvas.create_text(bar, middle, text="‹ ›", fill=BLUE, font=("Segoe UI", 13, "bold"))

    def refresh(self):
        self.choose.configure(state="disabled" if self.busy else "normal")
        self.run.configure(state="normal" if self.source is not None and not self.busy else "disabled")
        self.save.configure(state="normal" if self.result is not None and not self.busy else "disabled")
        self.update.configure(state="disabled" if self.busy else "normal")
        self.selector.configure(state="disabled" if self.busy else "readonly")
        self.noise.configure(state="disabled" if self.busy else "normal")
        self.draw()

    def work(self, status, task, done):
        self.busy = True
        self.status.set(status)
        self.refresh()
        future = self.pool.submit(task)

        def poll():
            if not future.done():
                self.root.after(60, poll)
                return
            self.busy = False
            try:
                result = future.result()
            except Exception as error:
                self.status.set("A operação não foi concluída.")
                messagebox.showerror("Fotos Aprimoradas", str(error), parent=self.root)
            else:
                done(result)
            self.refresh()
        self.root.after(60, poll)

    def open_photo(self):
        path = filedialog.askopenfilename(parent=self.root, title="Abrir foto",
                                          filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"),
                                                     ("Todos os arquivos", "*")])
        if path:
            self.work("Abrindo imagem…", lambda: load_photo(path), lambda photo: self.loaded(path, photo))

    def loaded(self, path, photo):
        self.path, self.source = Path(path), photo
        self.dimensions.set(f"{self.path.name}\n{photo.width} × {photo.height} px")
        self.invalidate()

    def invalidate(self, _=None):
        if self.source is not None:
            self.result = None
            self.caption.configure(text="Foto original")
            self.status.set("Escolha a escala e clique em Aprimorar foto.")
            self.refresh()

    def process(self):
        photo, scale, denoise = self.source, int(self.scale.get()[0]), self.denoise.get()
        self.work("Aprimorando foto…", lambda: enhance(photo, scale, denoise), self.processed)

    def processed(self, photo):
        self.result = photo
        self.caption.configure(text="Original à esquerda · aprimorada à direita")
        self.status.set(f"Resultado pronto · {photo.width} × {photo.height} px")

    def export(self):
        target = filedialog.asksaveasfilename(parent=self.root, title="Salvar resultado",
                                             initialdir=self.path.parent,
                                             initialfile=f"{self.path.stem}-aprimorada",
                                             defaultextension=".png",
                                             filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("WebP", "*.webp")])
        if not target:
            return
        if Path(target).resolve() == self.path.resolve():
            messagebox.showerror("Salvar resultado", "Escolha um nome diferente para preservar a foto original.")
            return
        photo = self.result
        self.work("Salvando imagem…", lambda: save_photo(photo, target),
                  lambda _: self.status.set(f"Salvo em {Path(target).name}"))

    def check_updates(self):
        self.work("Verificando atualizações…", get_asset, self.update_found)

    def update_found(self, asset):
        if asset is None:
            self.status.set("Você já está usando a versão mais recente.")
        elif messagebox.askyesno("Atualização disponível", f"Baixar e abrir o instalador {asset[0]}? Salve sua foto antes de atualizar."):
            self.work("Baixando e verificando o instalador…", lambda: download_and_launch(asset),
                      lambda _: self.status.set("Instalador aberto. Siga as etapas para atualizar."))
        else:
            self.status.set(f"Atualização disponível · {asset[0]}")

    def close(self):
        if self.busy:
            return
        self.pool.shutdown(wait=False)
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    App(window)
    window.mainloop()
