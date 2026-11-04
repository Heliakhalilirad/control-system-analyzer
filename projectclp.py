import tkinter as tk
from tkinter import ttk, messagebox
import control
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle
from PIL import Image, ImageTk


def get_root_tf():
    num = list(map(float, entry_num.get().split()))
    den = list(map(float, entry_den.get().split()))
    return control.TransferFunction(num, den)


def draw_root_locus_interactive():
    try:
        sys = get_root_tf()
        fig, ax = plt.subplots(figsize=(13,9))
        
        r_locus, k_values = control.root_locus(sys, grid=True, plot=False, kvect=np.logspace(-3, 3, 2000))
        current_poles = sys.poles()
        current_zeros = sys.zeros()
        
        for rl in r_locus.T:
            valid_points = np.isfinite(rl.real) & np.isfinite(rl.imag)
            if np.any(valid_points):
                ax.plot(rl.real[valid_points], rl.imag[valid_points], 
                       'b-', linewidth=2.2, alpha=0.8, zorder=5)
        
        pole_scat = ax.scatter(current_poles.real, current_poles.imag, c='red', s=180, 
                              marker='X', linewidth=4, label='Poles', picker=True, zorder=10)
        zero_scat = ax.scatter(current_zeros.real, current_zeros.imag, c='limegreen', s=180, 
                              marker='o', linewidth=4, label='Zeros', picker=True, zorder=10)
        
        ax.set_title("Root Locus Interactive", fontsize=16, fontweight="bold")
        ax.set_xlabel("Real", fontsize=12)
        ax.set_ylabel("Imag", fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.2)
        ax.axvline(x=0, color='k', linestyle='-', alpha=0.2)
        
        tf_label = fig.text(0.02, 0.02, f"TF: {sys}", fontsize=11, 
                          bbox=dict(boxstyle="round,pad=0.4", facecolor="lightblue", alpha=0.9))
        info_label = fig.text(0.02, 0.98, "", fontsize=10, va='top',
                             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9))
        k_label = fig.text(0.98, 0.02, "Click anywhere → Precise K value", fontsize=11, ha='right',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.9))
        
        selected_point = {"ind": None, "type": None}

        def on_pick(event):
            if event.artist == pole_scat:
                selected_point["ind"] = event.ind[0]
                selected_point["type"] = "pole"
            elif event.artist == zero_scat:
                selected_point["ind"] = event.ind[0]
                selected_point["type"] = "zero"

        def on_motion(event):
            if selected_point["ind"] is not None and event.inaxes:
                x, y = event.xdata, event.ydata
                ind = selected_point["ind"]
                if selected_point["type"] == "pole":
                    current_poles[ind] = complex(x, y)
                    pole_scat.set_offsets(np.column_stack((current_poles.real, current_poles.imag)))
                elif selected_point["type"] == "zero":
                    current_zeros[ind] = complex(x, y)
                    zero_scat.set_offsets(np.column_stack((current_zeros.real, current_zeros.imag)))
                fig.canvas.draw_idle()

        def on_release(event):
            selected_point["ind"] = None
            selected_point["type"] = None

        def update_root_locus(event):
            try:
                poles_clean = np.array([complex(round(p.real,6), round(p.imag,6)) for p in current_poles])
                zeros_clean = np.array([complex(round(z.real,6), round(z.imag,6)) for z in current_zeros])

                if len(zeros_clean) == 0:
                    zeros_clean = np.array([complex(-10,0)])
                while len(zeros_clean) < len(poles_clean):
                    zeros_clean = np.append(zeros_clean, complex(0,0))

                num_coeffs = np.poly(zeros_clean)
                den_coeffs = np.poly(poles_clean)
                new_tf = control.TransferFunction(num_coeffs, den_coeffs)
                
                new_r_locus, new_k_values = control.root_locus(new_tf, grid=False, plot=False, kvect=np.logspace(-3, 3, 2000))
                
                for line in ax.lines[:]:
                    if line.get_linewidth() == 2.2:
                        line.remove()
                
                for rl in new_r_locus.T:
                    valid_points = np.isfinite(rl.real) & np.isfinite(rl.imag)
                    if np.any(valid_points):
                        ax.plot(rl.real[valid_points], rl.imag[valid_points], 
                               'b-', linewidth=2.2, alpha=0.8, zorder=5)
                
                nonlocal r_locus, k_values
                r_locus = new_r_locus
                k_values = new_k_values
                
                tf_label.set_text(f"TF: {new_tf}")
                
                poles_display = [f"{p.real:.4f}{'±' if p.imag != 0 else ''}{abs(p.imag):.4f}j" 
                                 for p in current_poles]
                zeros_display = [f"{z.real:.4f}{'±' if z.imag != 0 else ''}{abs(z.imag):.4f}j" 
                                 for z in current_zeros]
                info_text = f"Poles: [{', '.join(poles_display)}]\nZeros: [{', '.join(zeros_display)}]"
                info_label.set_text(info_text)
                
                fig.canvas.draw_idle()
                
            except Exception as e:
                tf_label.set_text(f"Error: {str(e)[:50]}...")
                fig.canvas.draw_idle()


        def on_locus_click(event):
            if event.inaxes != ax or event.button != 1:
                return
            
            x, y = event.xdata, event.ydata
            if x is None or y is None:
                return
            
            for artist in list(ax.collections) + list(ax.lines) + list(ax.texts):
                try:
                    if artist.get_label() == '_k_marker':
                        artist.remove()
                except:
                    pass
            
            for patch in ax.patches[:]:
                if patch.get_label() == '_k_marker':
                    patch.remove()
            
            min_distance = float('inf')
            closest_k_idx = -1
            closest_root = None
            
            x_range = abs(ax.get_xlim()[1] - ax.get_xlim()[0])
            y_range = abs(ax.get_ylim()[1] - ax.get_ylim()[0])
            threshold = max(x_range, y_range) * 0.015
            
            for branch in r_locus.T:
                valid_mask = np.isfinite(branch.real) & np.isfinite(branch.imag)
                valid_indices = np.where(valid_mask)[0]
                
                for idx in valid_indices:
                    root = branch[idx]
                    distance = np.sqrt((root.real - x)**2 + (root.imag - y)**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_k_idx = idx
                        closest_root = root
            
            if closest_k_idx != -1 and min_distance < threshold:
                k_value = k_values[closest_k_idx]
                root_pos = closest_root
                
                ax.scatter([root_pos.real], [root_pos.imag], 
                          c='gold', s=220, marker='o',
                          edgecolors='darkred', linewidth=2.5, 
                          zorder=25, label='_k_marker')
                
                ax.axhline(y=root_pos.imag, color='orange', linestyle='--', 
                          alpha=0.6, linewidth=1.2, label='_k_marker')
                ax.axvline(x=root_pos.real, color='orange', linestyle='--', 
                          alpha=0.6, linewidth=1.2, label='_k_marker')
                
                if abs(root_pos.imag) < 1e-10:
                    root_str = f"{root_pos.real:.6f}"
                elif root_pos.imag >= 0:
                    root_str = f"{root_pos.real:.6f} + {abs(root_pos.imag):.6f}j"
                else:
                    root_str = f"{root_pos.real:.6f} - {abs(root_pos.imag):.6f}j"
                
                accuracy = 1 - (min_distance / threshold)
                
                info_text = f'k = {k_value:.6f}'
                
                info_box = ax.text(0.02, 0.98, info_text,
                                 transform=ax.transAxes,
                                 verticalalignment='top',
                                 fontsize=11,
                                 bbox=dict(boxstyle='round', 
                                          facecolor='gold', 
                                          alpha=0.95,
                                          edgecolor='darkred'),
                                 label='_k_marker')
                
                k_label.set_text(f"K = {k_value:.4f}")
                
                circle = plt.Circle((x, y), min_distance, 
                                   color='red', fill=False, 
                                   linestyle=':', alpha=0.4, linewidth=1)
                ax.add_patch(circle)
                circle.set_label('_k_marker')
                
                print("=" * 60)
                print("HIGH PRECISION K DETECTION")
                print("=" * 60)
                print(f"Click position:      ({x:.8f}, {y:.8f})")
                print(f"Locus point:         ({root_pos.real:.8f}, {root_pos.imag:.8f})")
                print(f"K value:             {k_value:.8f}")
                print(f"Distance:            {min_distance:.8f}")
                print(f"Threshold:           {threshold:.8f}")
                print(f"Accuracy:            {accuracy:.2%}")
                print("=" * 60)
                
                try:
                    tf_at_k = control.TransferFunction(sys.num * k_value, sys.den)
                    poles_at_k = tf_at_k.poles()
                    
                    poles_info = "\nPoles at this K:"
                    for i, pole in enumerate(poles_at_k):
                        if abs(pole.imag) < 1e-10:
                            pole_str = f"{pole.real:.6f}"
                        elif pole.imag >= 0:
                            pole_str = f"{pole.real:.6f} + {abs(pole.imag):.6f}j"
                        else:
                            pole_str = f"{pole.real:.6f} - {abs(pole.imag):.6f}j"
                        poles_info += f"\n  p{i+1}: {pole_str}"
                    
                    info_box.set_text(info_text + poles_info)
                except Exception as e:
                    print(f"Warning: Could not compute poles at K: {e}")
                
            else:
                k_label.set_text(f"Too far from locus (dist: {min_distance:.3f})")
                
                temp_text = ax.text(x, y, f"({x:.3f}, {y:.3f})", 
                                  fontsize=9, color='gray', alpha=0.7,
                                  bbox=dict(boxstyle='round', facecolor='white', alpha=0.7),
                                  label='_k_marker')
                
                fig.canvas.draw_idle()
                def remove_temp():
                    try:
                        temp_text.remove()
                        fig.canvas.draw_idle()
                    except:
                        pass
                
                fig.canvas.draw()
                plt.pause(0.8)
                try:
                    temp_text.remove()
                except:
                    pass
            
            fig.canvas.draw_idle()
        
        
        def on_scroll(event):
            if event.inaxes == ax:
                scale = 1.1 if event.button == 'up' else 0.9
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                x_center = (xlim[0] + xlim[1]) / 2
                y_center = (ylim[0] + ylim[1]) / 2
                new_width = (xlim[1] - xlim[0]) * scale
                new_height = (ylim[1] - ylim[0]) * scale
                ax.set_xlim([x_center - new_width/2, x_center + new_width/2])
                ax.set_ylim([y_center - new_height/2, y_center + new_height/2])
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect('pick_event', on_pick)
        fig.canvas.mpl_connect('motion_notify_event', on_motion)
        fig.canvas.mpl_connect('button_release_event', on_release)
        fig.canvas.mpl_connect('button_press_event', on_locus_click)
        fig.canvas.mpl_connect('scroll_event', on_scroll)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        messagebox.showerror("خطا", f"خطا در رسم Root Locus:\n{str(e)}")

def dominant_pole(sys):
    poles = control.poles(sys)
    stable_poles = [p for p in poles if np.real(p) < 0]
    return max(stable_poles, key=lambda p: np.real(p)) if stable_poles else poles[0]

def damping_from_pole(p):
    wn = abs(p)
    zeta = -np.real(p) / wn if wn != 0 else 0
    return wn, zeta


class DraggableBox:
    def __init__(self, fig, ax, text_content, initial_pos=(0.5, 0.05)):
        self.fig = fig
        self.ax = ax
        self.text_content = text_content
        self.pos = initial_pos
        self.dragging = False
        self.offset = (0, 0)
        
      
        self.box = self.ax.text(
            self.pos[0], self.pos[1], self.text_content,
            transform=self.ax.transAxes,
            fontsize=9,  
            verticalalignment='bottom',
            horizontalalignment='left',
            bbox=dict(
                boxstyle='round,pad=0.5', 
                facecolor='#dbeafe',
                edgecolor='#93c5fd',
                alpha=0.9, 
                linewidth=1.2
            ),
            color='#0f172a',
            family='monospace',
            picker=True
        )
        
      
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
    
    def update_content(self, new_text):
        self.text_content = new_text
        self.box.set_text(new_text)
        self.fig.canvas.draw_idle()
    
    def on_pick(self, event):
        if event.artist == self.box:
            self.dragging = True
            bbox = self.box.get_window_extent()
            x_click, y_click = event.mouseevent.x, event.mouseevent.y
            x_box, y_box = bbox.x0 + bbox.width/2, bbox.y0 + bbox.height/2
            self.offset = (x_box - x_click, y_box - y_click)
    
    def on_motion(self, event):
        if self.dragging and event.xdata is not None and event.ydata is not None:
            trans = self.ax.transAxes.inverted()
            new_pos = trans.transform((event.x + self.offset[0], event.y + self.offset[1]))
            new_pos = (max(0.02, min(0.98, new_pos[0])), 
                      max(0.02, min(0.98, new_pos[1])))
            self.pos = new_pos
            self.box.set_position(new_pos)
            self.fig.canvas.draw_idle()
    
    def on_release(self, event):
        self.dragging = False




def get_step_tf():
    if use_same_tf.get():
        return get_root_tf()
    num = list(map(float, entry_num_step.get().split()))
    den = list(map(float, entry_den_step.get().split()))
    return control.TransferFunction(num, den)

def plot_step_response():
    try:
        sys = get_step_tf()
        t, y = control.step_response(sys)
        
       
        y_final = y[-1]
        
       
        y_max = np.max(y)
        overshoot = ((y_max - y_final) / y_final) * 100 if y_final != 0 else 0
        
       
        tp_idx = np.argmax(y)
        tp = t[tp_idx] if tp_idx < len(t) else 0
        
       
        y_10 = 0.1 * y_final
        y_90 = 0.9 * y_final
        
        tr_start_idx = np.where(y >= y_10)[0]
        tr_end_idx = np.where(y >= y_90)[0]
        
        tr_start = t[tr_start_idx[0]] if len(tr_start_idx) > 0 else 0
        tr_end = t[tr_end_idx[0]] if len(tr_end_idx) > 0 else 0
        tr = tr_end - tr_start if tr_start > 0 and tr_end > 0 else 0
        
       
        y_50 = 0.5 * y_final
        td_idx = np.where(y >= y_50)[0]
        td = t[td_idx[0]] if len(td_idx) > 0 else 0
        
       
        settling_2_idx = np.where(np.abs(y - y_final) <= 0.02 * y_final)[0]
        settling_5_idx = np.where(np.abs(y - y_final) <= 0.05 * y_final)[0]
        
        ts_2 = t[settling_2_idx[0]] if len(settling_2_idx) > 0 else 0
        ts_5 = t[settling_5_idx[0]] if len(settling_5_idx) > 0 else 0
        
        p_dom = dominant_pole(sys)
        wn, zeta_real = damping_from_pole(p_dom)
        
        fig, ax = plt.subplots(figsize=(11,7))
        ax.plot(t, y, linewidth=2.5, label="Real System", color='#1e40af')
        
      
        ax.plot(tp, y_max, 'ro', markersize=8, label=f'Peak (tp={tp:.3f}s)')
        ax.axvline(x=tp, color='r', linestyle='--', alpha=0.5)
        ax.axhline(y=y_max, color='r', linestyle='--', alpha=0.5)
        
       
        if ts_2 > 0:
            ax.axvline(x=ts_2, color='purple', linestyle='--', alpha=0.7, label=f'Settling 2% (ts={ts_2:.3f}s)')
            ax.axhline(y=y_final*0.98, color='purple', linestyle=':', alpha=0.3)
            ax.axhline(y=y_final*1.02, color='purple', linestyle=':', alpha=0.3)
        
        if ts_5 > 0:
            ax.axvline(x=ts_5, color='brown', linestyle='--', alpha=0.7, label=f'Settling 5% (ts={ts_5:.3f}s)')
            ax.axhline(y=y_final*0.95, color='brown', linestyle=':', alpha=0.3)
            ax.axhline(y=y_final*1.05, color='brown', linestyle=':', alpha=0.3)
        
       
        if tr_start > 0 and tr_end > 0:
            ax.axvline(x=tr_start, color='green', linestyle='--', alpha=0.7, label=f'Rise start (tr_start={tr_start:.3f}s)')
            ax.axvline(x=tr_end, color='blue', linestyle='--', alpha=0.7, label=f'Rise end (tr_end={tr_end:.3f}s)')
        
        
        if td > 0:
            ax.axvline(x=td, color='orange', linestyle='--', alpha=0.7, label=f'Delay time (td={td:.3f}s)')
        
        if compare_mode.get():
            zeta_new = float(entry_zeta_new.get())
            sys_ref = control.TransferFunction([wn**2], [1, 2*zeta_new*wn, wn**2])
            t2, y2 = control.step_response(sys_ref, T=t)
            ax.plot(t2, y2, '--', linewidth=2.5, label=f"2nd Order (ζ={zeta_new:.2f})", color='red')
        
        if compare_wn_mode.get():
            wn_new = float(entry_wn_new.get())
            if compare_mode.get():
                zeta_to_use = float(entry_zeta_new.get())
            else:
                zeta_to_use = zeta_real
                
            sys_ref_wn = control.TransferFunction([wn_new**2], [1, 2*zeta_to_use*wn_new, wn_new**2])
            t3, y3 = control.step_response(sys_ref_wn, T=t)
            ax.plot(t3, y3, ':', linewidth=2.5, label=f"2nd Order (ζ={zeta_to_use:.2f}, ωn={wn_new:.2f})", color='green')
        
        ax.set_title("Step Response Analysis with Performance Metrics", fontsize=15, fontweight="bold")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Response")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9, loc='upper right')
        
      
        info_text = f"""╔══════════════════════════════════════╗
║    STEP RESPONSE SPECIFICATIONS    ║
╠══════════════════════════════════════╣
║ Overshoot : {overshoot:>6.2f} %           ║
║ Peak Time : {tp:>6.3f} s           ║
║ Rise Time : {tr:>6.3f} s (10-90%)  ║
║ Settling 2% : {ts_2:>6.3f} s         ║
║ Settling 5% : {ts_5:>6.3f} s         ║
║ Steady State: {y_final:>6.3f}           ║
╠══════════════════════════════════════╣
║ ωn : {wn:>6.3f} rad/s           ║
║ ζ  : {zeta_real:>6.3f}           ║
╚══════════════════════════════════════╝"""
        
      
        draggable_box = DraggableBox(fig, ax, info_text, initial_pos=(0.02, 0.95))
        
       
        help_text = ax.text(0.5, 0.01, "📦 Drag to move", 
                           transform=ax.transAxes, fontsize=8, 
                           color='gray', ha='center', 
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        plt.tight_layout()
        plt.show()
        
      
        specs_text = f"""STEP RESPONSE SPECIFICATIONS
────────────────────────────
Overshoot: {overshoot:.2f}%
Peak Time (tp): {tp:.3f} s
Rise Time (tr): {tr:.3f} s
Delay Time (td): {td:.3f} s
Settling Time (2%): {ts_2:.3f} s
Settling Time (5%): {ts_5:.3f} s
────────────────────────────
Steady State: {y_final:.3f}
ωn: {wn:.3f} rad/s
ζ: {zeta_real:.3f}"""
        
        specs_label.config(text=specs_text, font=("Consolas", 10, "bold"), fg="#1e40af")
        
        print("="*60)
        print("STEP RESPONSE PERFORMANCE METRICS")
        print("="*60)
        print(f"Overshoot (OS): {overshoot:.4f}%")
        print(f"Peak Time (tp): {tp:.6f} s")
        print(f"Rise Time (tr): {tr:.6f} s (10% to 90%)")
        print(f"Delay Time (td): {td:.6f} s (to 50%)")
        print(f"Settling Time (ts2%): {ts_2:.6f} s")
        print(f"Settling Time (ts5%): {ts_5:.6f} s")
        print(f"Steady State Value: {y_final:.6f}")
        print("="*60)
        
    except Exception as e:
        messagebox.showerror("خطا", f"خطا در Step Response:\n{str(e)}")

def toggle_step_entries():
    state = "disabled" if use_same_tf.get() else "normal"
    entry_num_step.config(state=state)
    entry_den_step.config(state=state)

def toggle_compare_entry():
    state = "normal" if compare_mode.get() else "disabled"
    entry_zeta_new.config(state=state)

def toggle_compare_wn_entry():
    state = "normal" if compare_wn_mode.get() else "disabled"
    entry_wn_new.config(state=state)



root = tk.Tk()
root.title("Control System Interactive Analyzer - High Precision")
root.geometry("1200x900")
root.configure(bg="#f8fafc")

style = ttk.Style()
style.theme_use("default")
style.configure("TNotebook.Tab", background="#e2e8f0", foreground="#1e293b",
                padding=[15,8], font=("Segoe UI",11,"bold"))
style.map("TNotebook.Tab", background=[("selected","#3b82f6")], foreground=[("selected","white")])

left_frame = tk.Frame(root, bg="#f8fafc")
left_frame.pack(side=tk.LEFT, padx=(20,10), pady=15, fill=tk.Y)

try:
    logo_image = Image.open("image.jpg")
    logo_image = logo_image.resize((80, 80), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(left_frame, image=logo_photo, bg="#f8fafc")
    logo_label.image = logo_photo
    logo_label.pack(pady=(0,10))
except:
    logo_label = tk.Label(left_frame, text="📊", font=("Segoe UI", 40), bg="#f8fafc", fg="#3b82f6")
    logo_label.pack(pady=(0,10))

title = tk.Label(left_frame, text="Control System Analyzer", 
                bg="#f8fafc", fg="#1e40af", font=("Segoe UI",22,"bold"))
title.pack()

subtitle = tk.Label(left_frame, text="Root Locus and Step Response Analysis",
                   bg="#f8fafc", fg="#64748b", font=("Segoe UI",12))
subtitle.pack()

right_frame = tk.Frame(root, bg="#f8fafc")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0,20), pady=15)

notebook = ttk.Notebook(right_frame)
notebook.pack(expand=True, fill="both", padx=10, pady=10)


tab1 = tk.Frame(notebook, bg="#f1f5f9")
notebook.add(tab1, text="📈 Root Locus")

tk.Label(tab1, text="Numerator (b0 b1 b2 ...):", bg="#f1f5f9", fg="#1e293b", 
         font=("Segoe UI",11,"bold")).pack(pady=(20,5))
entry_num = ttk.Entry(tab1, width=40, font=("Consolas",11))
entry_num.insert(0, "1"); entry_num.pack(pady=(0,10))

tk.Label(tab1, text="Denominator (a0 a1 a2 ...):", bg="#f1f5f9", fg="#1e293b", 
         font=("Segoe UI",11,"bold")).pack(pady=(0,5))
entry_den = ttk.Entry(tab1, width=40, font=("Consolas",11))
entry_den.insert(0, "1 3 2"); entry_den.pack(pady=(0,30))

tk.Button(tab1, text="🎯 Draw Root Locus", command=draw_root_locus_interactive,
          bg="#3b82f6", fg="white", font=("Segoe UI",12,"bold"), relief="flat",
          padx=30, pady=10, cursor="hand2").pack(pady=20)


tab2 = tk.Frame(notebook, bg="#f1f5f9")
notebook.add(tab2, text="📊 Step Response")

use_same_tf = tk.BooleanVar(value=True)
compare_mode = tk.BooleanVar(value=False)
compare_wn_mode = tk.BooleanVar(value=False)

tk.Checkbutton(tab2, text="Use same TF from Root Locus", variable=use_same_tf, 
               command=toggle_step_entries, bg="#f1f5f9", fg="#1e293b", 
               font=("Segoe UI",11,"bold")).pack(pady=(20,15))

tk.Label(tab2, text="Numerator:", bg="#f1f5f9", fg="#1e293b", font=("Segoe UI",11,"bold")).pack()
entry_num_step = ttk.Entry(tab2, width=40, font=("Consolas",11))
entry_num_step.insert(0, "1")
entry_num_step.pack(pady=(0,10))

tk.Label(tab2, text="Denominator:", bg="#f1f5f9", fg="#1e293b", font=("Segoe UI",11,"bold")).pack()
entry_den_step = ttk.Entry(tab2, width=40, font=("Consolas",11))
entry_den_step.insert(0, "1 3 2")
entry_den_step.pack(pady=(0,20))

toggle_step_entries()

tk.Checkbutton(tab2, text="Compare with 2nd-order model (different ζ)", 
               variable=compare_mode, 
               command=toggle_compare_entry, bg="#f1f5f9", fg="#1e293b", 
               font=("Segoe UI",11,"bold")).pack(pady=(0,10))

frame_zeta = tk.Frame(tab2, bg="#f1f5f9")
tk.Label(frame_zeta, text="New ζ:", bg="#f1f5f9", fg="#1e293b", 
         font=("Segoe UI",11,"bold")).pack(side=tk.LEFT)
entry_zeta_new = ttk.Entry(frame_zeta, width=12, font=("Consolas",11))
entry_zeta_new.insert(0, "0.6")
entry_zeta_new.pack(side=tk.LEFT, padx=(10,0))
frame_zeta.pack(pady=(0,10))

toggle_compare_entry()

tk.Checkbutton(tab2, text="Compare with 2nd-order model (different ωn)", 
               variable=compare_wn_mode, 
               command=toggle_compare_wn_entry, bg="#f1f5f9", fg="#1e293b", 
               font=("Segoe UI",11,"bold")).pack(pady=(0,10))

frame_wn = tk.Frame(tab2, bg="#f1f5f9")
tk.Label(frame_wn, text="New ωn:", bg="#f1f5f9", fg="#1e293b", 
         font=("Segoe UI",11,"bold")).pack(side=tk.LEFT)
entry_wn_new = ttk.Entry(frame_wn, width=12, font=("Consolas",11))
entry_wn_new.insert(0, "2.0")
entry_wn_new.pack(side=tk.LEFT, padx=(10,0))
frame_wn.pack(pady=(0,15))

toggle_compare_wn_entry()

tk.Button(tab2, text="🚀 Plot Step Response", command=plot_step_response,
          bg="#3b82f6", fg="white", font=("Segoe UI",12,"bold"), relief="flat",
          padx=35, pady=10, cursor="hand2").pack(pady=25)

specs_label = tk.Label(tab2, text="System specs will appear here...", bg="#f1f5f9", 
                      fg="#059669", font=("Consolas", 9, "bold"), 
                      relief="ridge", padx=15, pady=10, justify=tk.LEFT, anchor=tk.W)
specs_label.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

root.mainloop()