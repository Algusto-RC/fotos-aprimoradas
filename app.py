from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from PIL import Image, ImageFilter, ImageOps, ImageTk

from enhance import enhance, load_photo, save_photo
from updates import VERSION, download_and_launch, get_asset

INK = "#142D25"
MUTED = "#48665A"
GREEN = "#1DB36F"
MINT = "#43FFAA"
WHITE = "#FFFFFF"
ICE = "#F2FFF9"
BORDER = "#CAE9DB"
STAGE = "#17342D"
ERROR = "#B3220B"
PEACH = "#FFB5AA"
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
        self.detail = tk.StringVar(value="Equilibrado")
        self.zoomed = False
        self.view_center = (0.5, 0.5)
        self.drag_position = None
        self.bounds = (0, 1)
        self.status = tk.StringVar(value="Abra uma foto para começar.")
        self.dimensions = tk.StringVar(value="JPG, PNG, WebP, BMP ou TIFF")
        root.title("Fotos Aprimoradas · Lab Gusto")
        root.geometry("1120x740")
        root.minsize(840, 620)
        root.configure(fg_color=ICE)
        root.protocol("WM_DELETE_WINDOW", self.close)

        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(20, 16))
        self.label(header, "lab.gusto", 13, MUTED, bold=True).pack(anchor="w")
        self.label(header, "Fotos Aprimoradas", 36, INK, bold=True).pack(anchor="w")
        main = ctk.CTkFrame(root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=28)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)
        compare = self.card(main)
        compare.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        panel = self.card(main, width=276)
        panel.grid(row=0, column=1, sticky="ns")
        panel.pack_propagate(False)

        toolbar = ctk.CTkFrame(compare, fg_color="transparent")
        toolbar.pack(fill="x", padx=14, pady=(12, 8))
        self.label(toolbar, "Prévia", 17, INK, bold=True).pack(side="left")
        self.zoom_button = self.button(toolbar, "Zoom 100%", self.toggle_zoom, width=104, height=30)
        self.zoom_button.pack(side="right")
        self.canvas = tk.Canvas(compare, bg=STAGE, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14)
        self.canvas.bind("<Configure>", lambda _: self.draw())
        self.canvas.bind("<Button-1>", self.move_split)
        self.canvas.bind("<B1-Motion>", self.move_split)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan)
        self.slider = ctk.CTkSlider(compare, from_=0, to=100, variable=self.split,
                                    fg_color=BORDER, progress_color=GREEN,
                                    button_color=INK, button_hover_color=GREEN,
                                    command=lambda _: self.draw())
        self.slider.pack(fill="x", padx=17, pady=(9, 0))
        self.caption = self.label(compare, "Demonstração · arraste para comparar", 12, MUTED)
        self.caption.pack(anchor="w", padx=14, pady=(0, 9))

        self.label(panel, "Sua foto", 20, INK, bold=True).pack(anchor="w", padx=17, pady=(15, 8))
        self.choose = self.button(panel, "Abrir imagem…", self.open_photo)
        self.choose.pack(fill="x", padx=17)
        self.file_label = ctk.CTkLabel(panel, textvariable=self.dimensions, anchor="w", justify="left",
                                      wraplength=240, text_color=MUTED, font=("Segoe UI", 12))
        self.file_label.pack(fill="x", padx=17, pady=(4, 10))
        self.label(panel, "Ampliação", 13, INK, bold=True).pack(anchor="w", padx=17)
        self.selector = ctk.CTkSegmentedButton(
            panel, values=["1×", "2×", "3×", "4×"], variable=self.scale,
            command=self.invalidate, selected_color=MINT, selected_hover_color=GREEN,
            unselected_color="#DCEFE6", unselected_hover_color=BORDER,
            fg_color="#DCEFE6", text_color=INK, height=35)
        self.selector.pack(fill="x", padx=17, pady=(3, 10))
        self.label(panel, "Aprimoramento", 13, INK, bold=True).pack(anchor="w", padx=17)
        self.profile = ctk.CTkOptionMenu(
            panel, values=["Suave", "Equilibrado", "Detalhes"], variable=self.detail,
            command=self.invalidate, fg_color="#DCEFE6", button_color=BORDER,
            button_hover_color=GREEN, text_color=INK, dropdown_fg_color=ICE,
            dropdown_text_color=INK, height=35)
        self.profile.pack(fill="x", padx=17, pady=(3, 13))
        self.run = self.button(panel, "Aprimorar foto", self.process, primary=True)
        self.run.pack(fill="x", padx=17)
        self.save = self.button(panel, "Salvar resultado", self.export)
        self.save.pack(fill="x", padx=17, pady=(7, 0))
        self.label(panel, "Processamento local", 11, MUTED).pack(side="bottom", anchor="w", padx=17, pady=9)

        footer = ctk.CTkFrame(root, fg_color="transparent")
        footer.pack(fill="x", padx=28, pady=10)
        self.status_label = ctk.CTkLabel(footer, textvariable=self.status, text_color=MUTED,
                                         font=("Segoe UI", 12), wraplength=580, justify="left")
        self.status_label.pack(side="left")
        self.update = self.button(footer, "⟳", self.check_updates, width=36, height=34)
        self.update.pack(side="right")
        self.update_text = self.label(footer, "", 12, MUTED)
        self.update_text.pack(side="right", padx=8)
        self.update.bind("<Enter>", lambda _: self.update_text.configure(text="Verificar atualizações"))
        self.update.bind("<Leave>", lambda _: self.update_text.configure(text=""))
        self.label(footer, f"v{VERSION}", 12, MUTED).pack(side="right")
        self.demo = self.read_demo()
        self.refresh()

    @staticmethod
    def card(parent, **kwargs):
        return ctk.CTkFrame(parent, fg_color=WHITE, border_color=BORDER,
                            border_width=1, corner_radius=20, **kwargs)

    @staticmethod
    def label(parent, text, size, color, bold=False):
        return ctk.CTkLabel(parent, text=text, text_color=color,
                            font=("Segoe UI", size, "bold" if bold else "normal"))

    @staticmethod
    def button(parent, text, action, primary=False, **kwargs):
        kwargs.setdefault("height", 38)
        return ctk.CTkButton(parent, text=text, command=action, corner_radius=10,
                             fg_color=MINT if primary else "#E5F6ED", text_color=INK,
                             text_color_disabled=MUTED, hover_color=GREEN if primary else BORDER, border_width=0 if primary else 1,
                             border_color=BORDER,
                             font=("Segoe UI", 14, "bold"), **kwargs)

    @staticmethod
    def read_demo():
        try:
            image = load_photo(ASSETS / "demo.jpg")
            image.thumbnail((1440, 980))
            return image
        except OSError:
            return None

    def move_split(self, event):
        x, width = self.bounds
        self.split.set(max(0, min(100, round(100 * (event.x - x) / width))))
        self.draw()

    def toggle_zoom(self):
        self.zoomed = not self.zoomed
        self.zoom_button.configure(text="Ajustar à tela" if self.zoomed else "Zoom 100%")
        self.update_caption()
        self.draw()

    def start_pan(self, event):
        self.drag_position = event.x, event.y

    def pan(self, event):
        if not self.zoomed or self.drag_position is None:
            return
        old_x, old_y = self.drag_position
        photo = self.result or self.source or self.demo
        cx, cy = self.view_center
        self.view_center = (
            min(1, max(0, cx + (old_x - event.x) / photo.width)),
            min(1, max(0, cy + (old_y - event.y) / photo.height)),
        )
        self.drag_position = event.x, event.y
        self.draw()

    def draw(self):
        canvas = self.canvas
        width, height = canvas.winfo_width(), canvas.winfo_height()
        photo = self.result or self.source or self.demo
        if min(width, height) < 4 or photo is None:
            return
        canvas.delete("all")
        key = (photo, width, height, self.zoomed, self.view_center)
        if self.preview_key != key:
            if self.zoomed:
                w, h = min(width, photo.width), min(height, photo.height)
                cx, cy = self.view_center
                x = min(photo.width - w, max(0, round(cx * photo.width - w / 2)))
                y = min(photo.height - h, max(0, round(cy * photo.height - h / 2)))
                box = (x, y, x + w, y + h)
                after = photo.crop(box)
                if self.result is not None:
                    scale = photo.width / self.source.width
                    before = self.source.resize((w, h), Image.Resampling.LANCZOS,
                                                box=tuple(v / scale for v in box))
                else:
                    before = after
            else:
                after = ImageOps.contain(photo, (width, height), Image.Resampling.LANCZOS)
                before = self.source.resize(after.size, Image.Resampling.LANCZOS) if self.result is not None else after
            if self.source is None:
                before = after.filter(ImageFilter.GaussianBlur(5))
            self.layers = after, before
            self.preview_key = key
        after, before = self.layers
        x, y = (width - after.width) // 2, (height - after.height) // 2
        self.bounds = x, after.width
        cut = round(after.width * self.split.get() / 100)
        comparing = self.result is not None or self.source is None
        if comparing and cut:
            after = after.copy()
            after.paste(before.crop((0, 0, cut, after.height)), (0, 0))
        self.preview = ImageTk.PhotoImage(after)
        canvas.create_image(x, y, anchor="nw", image=self.preview)
        if comparing:
            bar = x + cut
            middle = height / 2
            canvas.create_line(bar, y, bar, y + after.height, width=2, fill=MINT)
            canvas.create_oval(bar - 13, middle - 13, bar + 13, middle + 13, fill=MINT, outline=INK)
            canvas.create_text(bar, middle, text="‹ ›", fill=INK, font=("Segoe UI", 12, "bold"))

    def update_caption(self):
        if self.source is None:
            text = "Demonstração · arraste para comparar"
        elif self.result is None:
            text = "Foto original"
        else:
            text = "Original à esquerda · aprimorada à direita"
        if self.zoomed:
            text += "  |  Mova com o botão direito"
        self.caption.configure(text=text)

    def refresh(self):
        self.choose.configure(state="disabled" if self.busy else "normal")
        self.run.configure(state="normal" if self.source is not None and not self.busy else "disabled")
        self.save.configure(state="normal" if self.result is not None and not self.busy else "disabled")
        self.update.configure(state="disabled" if self.busy else "normal")
        self.selector.configure(state="disabled" if self.busy else "normal")
        self.profile.configure(state="disabled" if self.busy else "normal")
        self.slider.configure(state="normal" if self.result is not None or self.source is None else "disabled")
        self.draw()

    def work(self, status, task, done):
        self.busy = True
        self.status_label.configure(text_color=MUTED, fg_color="transparent")
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
                self.status_label.configure(text_color=ERROR, fg_color=PEACH)
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
        self.view_center = (0.5, 0.5)
        self.split.set(50)
        self.dimensions.set(f"{self.path.name}\n{photo.width} × {photo.height} px")
        self.invalidate()

    def invalidate(self, _=None):
        if self.source is not None:
            self.result = None
            self.update_caption()
            self.status.set("Escolha a escala e clique em Aprimorar foto.")
            self.refresh()

    def process(self):
        photo, scale, profile = self.source, int(self.scale.get()[0]), self.detail.get()
        self.work("Aprimorando foto…", lambda: enhance(photo, scale, profile), self.processed)

    def processed(self, photo):
        self.result = photo
        self.update_caption()
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
    ctk.set_appearance_mode("light")
    window = ctk.CTk()
    App(window)
    window.mainloop()
