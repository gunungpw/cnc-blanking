import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk


def tool_back(code, z_init_post, safe_tool_distance, tool_diameter, workpiece_thickness):
    code.append(f"G00 Z{(z_init_post):.2f}")  # Move to safe height
    code.append(
        f"G00 X{-safe_tool_distance - (tool_diameter / 2)} Y{workpiece_thickness / 2:.2f}"
    )  # Move to starting position (slightly before material)


def start_coolant(code):
    code.append("M08")


def stop_coolant(code):
    code.append("M09")


def tool_offset(code, z_height):
    code.append(f"G43 H04 Z{z_height}")


def pause_process(code, spindle_speed):
    code.append("M00")  # Program stop
    code.append(f"M03 S{spindle_speed}")  # Spindle on after resume


def debug_message(message, just_clean_depth, remaining_stock, num_passes):
    print(f"{message} Cut")
    print(f"Just clean depth: {just_clean_depth:.2f} mm")
    print(f"Remaining stock: {remaining_stock:.2f} mm")
    print(f"Number of adjustment passes: {num_passes}")


def tool_spindle_stop(code):
    code.append("M05")  # Spindle stop


def tool_zero_return(code, all_axis=False, y_z_axis=False):
    if all_axis is True:  # zero return on start and end program
        code.append("G91 G30 Z0.0")
        code.append("G91 G28 Y0.0")
        code.append("G91 G30 X0.0")
    if y_z_axis is True:  # zero return on start of process
        code.append("G91 G28 Z0.0")
        code.append("G91 G28 Y0.0")


def reset_coordinate(code):
    code.append("G90 G00 G54 X0.0 Y0.0")


def generate_face_mill_gcode(
    workpiece_long=100.0,  # Long side of material (mm)
    workpiece_short=50.0,  # Short side of material (mm)
    workpiece_thick=20.0,  # Thick side of material (mm)
    parallel_block_long=0.0,  # Parallel block for long side (mm)
    parallel_block_short=0.0,  # Parallel block for short side (mm)
    long_stock_thickness=5.0,  # Long material thickness (mm)
    short_stock_thickness=3.0,  # Short material thickness (mm)
    tool_diameter=50.0,  # Face mill diameter (mm)
    feed_rate=500.0,  # Feed rate (mm/min)
    spindle_speed=2000,  # Spindle speed (RPM)
    depth_of_cut=1.0,  # Depth of cut per pass in adjustment (mm)
    safe_z_distance=20.0,  # Safe Z distance for rapid moves (mm)
    safe_tool_distance=5.0,  # Safe X distance for rapid moves (mm)
    just_clean_fraction=0.1,  # Fraction of stock_thickness for just clean (10% default)
    debug=False,  # Debug switch
):
    ### JUST CLEAN LONG SIDE ###
    # Calculate just_clean_depth as a fraction of stock_thickness
    just_clean_depth = long_stock_thickness * just_clean_fraction
    just_clean_depth = max(0.1, min(just_clean_depth, 0.5))  # Limit between 0.1mm and 0.5mm

    # Remaining stock after just clean
    remaining_stock = long_stock_thickness - just_clean_depth

    # Calculate number of adjustment passes based on remaining stock
    num_passes = int(remaining_stock / depth_of_cut) + (remaining_stock % depth_of_cut > 0)

    if debug is True:
        debug_message("Long", just_clean_depth, remaining_stock, num_passes)

    # Initialize G-code list
    gcode = []

    # Header
    gcode.append("%")  # Program start
    gcode.append("O0131")  # Program Number
    gcode.append("G00 G40 G49 G80")  # Rapid Positioning, Cancel offsets
    gcode.append("G21 G90 G54")  # Metric, Absolute, G54 coordinate system
    tool_zero_return(gcode, all_axis=True)
    reset_coordinate(gcode)
    gcode.append("(FACEMILL DIA. 63)")
    gcode.append("M06 T10")  # Tool change to face mill
    gcode.append(f"M03 S{spindle_speed}")  # Spindle start

    # Long side Z-position (top of workpiece_short + safe height)
    z_long_init = workpiece_short + safe_z_distance + parallel_block_long
    tool_offset(gcode, z_long_init)

    # Current Y position and direction for zigzag
    direction = 1  # 1 for forward, -1 for reverse

    gcode.append("(JUST CLEAN SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)

    # Just clean pass
    start_coolant(gcode)
    gcode.append(f"G01 Z{workpiece_short + parallel_block_long - just_clean_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
    gcode.append(
        f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{feed_rate / 2:.1f}"
    )  # Cut
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, spindle_speed)
    reset_coordinate(gcode)
    tool_offset(gcode, z_height=z_long_init)

    ### ADJUSTMENT LONG SIDE ###
    gcode.append("(ADJUSTMENT SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)
    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > long_stock_thickness:
            current_depth = long_stock_thickness  # Cap at long stock thickness

        # Generate cutting moves
        gcode.append(f"G01 Z{workpiece_short + parallel_block_long - current_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
        if direction == 1:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = -1
        else:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = 1
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, spindle_speed)
    reset_coordinate(gcode)
    tool_offset(gcode, z_height=z_long_init)

    ### JUST CLEAN SHORT SIDE ###
    # Calculate just_clean_depth as a fraction of stock_thickness
    just_clean_depth = short_stock_thickness * just_clean_fraction
    just_clean_depth = max(0.1, min(just_clean_depth, 0.5))  # Limit between 0.1mm and 0.5mm

    # Remaining stock after just clean
    remaining_stock = short_stock_thickness - just_clean_depth

    # Calculate number of adjustment passes based on remaining stock
    num_passes = int(remaining_stock / depth_of_cut) + (remaining_stock % depth_of_cut > 0)

    if debug is True:
        debug_message("Short", just_clean_depth, remaining_stock, num_passes)

    direction = 1  # 1 for forward, -1 for reverse

    z_short_init = workpiece_long + safe_z_distance + parallel_block_long  # Adjusted for short side
    gcode.append("(JUST CLEAN SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)

    # Just clean pass
    start_coolant(gcode)
    gcode.append(f"G01 Z{workpiece_long + parallel_block_short - just_clean_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
    gcode.append(
        f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{feed_rate / 2:.1f}"
    )  # Cut
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)
    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, spindle_speed)
    reset_coordinate(gcode)
    tool_offset(gcode, z_short_init)

    ### ADJUSTMENT SHORT SIDE ###
    gcode.append("(ADJUSTMENT SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)
    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > short_stock_thickness:
            current_depth = short_stock_thickness  # Cap at short stock thickness

        # Generate cutting moves
        gcode.append(f"G01 Z{workpiece_long + parallel_block_short - current_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
        if direction == 1:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = -1
        else:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = 1

    # Program end
    stop_coolant(gcode)
    tool_spindle_stop(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    gcode.append("M30")  # Program end
    gcode.append("%")  # End of file

    return gcode


def save_gcode_to_file(gcode_lines, filename="face_mill.nc"):
    """Save G-code to a file"""
    with open(filename, "w") as f:
        for line in gcode_lines:
            f.write(line + "\n")


class GCodeGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic Blanking")
        self.root.geometry("300x400")

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W + tk.E + tk.N + tk.S))

        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W + tk.E + tk.N + tk.S))

        # Tab 1: Workpiece Settings
        workpiece_frame = ttk.Frame(notebook, padding="5")
        notebook.add(workpiece_frame, text="Workpiece Settings")

        # Tab 2: Tool Settings
        tool_frame = ttk.Frame(notebook, padding="5")
        notebook.add(tool_frame, text="Tool Settings")

        # Parameters and their default values
        self.parameters = {
            "workpiece_long": 150.0,
            "workpiece_short": 50.0,
            "workpiece_thick": 20.0,
            "parallel_block_long": 0.0,
            "parallel_block_short": 0.0,
            "long_stock_thickness": 5.0,
            "short_stock_thickness": 3.0,
            "tool_diameter": 50.0,
            "feed_rate": 500.0,
            "spindle_speed": 2000.0,
            "depth_of_cut": 1.0,
            "safe_z_distance": 20.0,
            "safe_tool_distance": 5.0,
            "just_clean_fraction": 0.1,
            "debug": False,
        }

        # Split parameters into two groups (excluding debug from numeric entries)
        workpiece_params = [
            "workpiece_long",
            "workpiece_short",
            "workpiece_thick",
            "parallel_block_long",
            "parallel_block_short",
            "long_stock_thickness",
            "short_stock_thickness",
        ]
        tool_params = [
            "tool_diameter",
            "feed_rate",
            "spindle_speed",
            "depth_of_cut",
            "safe_z_distance",
            "safe_tool_distance",
            "just_clean_fraction",
        ]

        # Entries dictionary
        self.entries = {}

        # Workpiece Settings Tab
        row = 0
        for param in workpiece_params:
            label_text = param.replace("_", " ").title()
            ttk.Label(workpiece_frame, text=f"{label_text}", width=20, anchor="e").grid(
                row=row, column=0, pady=2, padx=2
            )
            self.entries[param] = ttk.Entry(workpiece_frame, width=10)
            self.entries[param].grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            self.entries[param].insert(0, str(self.parameters[param]))

            units = "mm" if "fraction" not in param else "%"
            ttk.Label(workpiece_frame, text=units, width=10).grid(row=row, column=2, sticky=tk.W, pady=2)
            row += 1

        # Tool Settings Tab
        row = 0
        for param in tool_params:
            label_text = param.replace("_", " ").title()
            ttk.Label(
                tool_frame,
                text=f"{label_text}",
                width=20,
                anchor="e",
            ).grid(row=row, column=0, pady=2, padx=2)
            self.entries[param] = ttk.Entry(tool_frame, width=10)
            self.entries[param].grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            self.entries[param].insert(0, str(self.parameters[param]))

            units = "mm" if "fraction" not in param else "%"
            if param == "feed_rate":
                units = "mm/min"
            elif param == "spindle_speed":
                units = "RPM"
            ttk.Label(tool_frame, text=units, width=10).grid(row=row, column=2, sticky=tk.W, pady=2)
            row += 1

        # Add Debug checkbox
        self.debug_var = tk.BooleanVar(value=self.parameters["debug"])
        debug_check = ttk.Checkbutton(
            tool_frame,
            text="Debug Mode",
            variable=self.debug_var,
            onvalue=True,
            offvalue=False,
        )
        debug_check.grid(row=row, column=0, columnspan=3, pady=2, sticky=tk.W)

        # Filename entry (outside tabs, in main frame)
        ttk.Label(main_frame, text="Output Filename").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.filename_entry = ttk.Entry(main_frame, width=25)
        self.filename_entry.grid(row=2, column=0, sticky=(tk.W + tk.E), pady=2)
        self.filename_entry.insert(0, "facemill_zigzag")

        # Generate button
        self.generate_btn = ttk.Button(main_frame, text="Generate NC Program", command=self.generate_gcode)
        self.generate_btn.grid(row=3, column=0, sticky=tk.W, pady=20)

        # Status label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=4, column=0, columnspan=3)

        # Configure column weights
        main_frame.columnconfigure(1, weight=1)
        workpiece_frame.columnconfigure(1, weight=1)
        tool_frame.columnconfigure(1, weight=1)

    def generate_gcode(self):
        try:
            # Get parameters from entries
            params = {}
            for param in self.parameters:
                if param == "debug":
                    params[param] = self.debug_var.get()
                else:
                    value = float(self.entries[param].get())
                    if value < 0 and param[:8] == "parallel":
                        raise ValueError(f"{param.replace('_', ' ').title()} must be positive or zero")
                    elif value <= 0 and param[:8] != "parallel":
                        raise ValueError(f"{param.replace('_', ' ').title()} must be positive and not zero")
                    params[param] = value

            # Generate G-code
            gcode = generate_face_mill_gcode(**params)
            # Current Time
            current_date = datetime.now().strftime("%Y%m%d")
            # Save to file
            filename = self.filename_entry.get()
            if not filename.endswith(".nc"):
                filename += ".nc"
            filename = f"{current_date}_{filename}"
            save_gcode_to_file(gcode, filename)

            # Show generated G-code in a new window
            self.show_gcode_window(gcode)

            self.status_label.config(text=f"Generated and saved to {filename}")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_gcode_window(self, gcode):
        # Create new window for G-code preview
        preview_window = tk.Toplevel(self.root)
        filename = self.filename_entry.get()
        # Current Time
        current_date = datetime.now().strftime("%Y%m%d")
        if not filename.endswith(".nc"):
            filename += ".nc"
        filename = f"{current_date}_{filename}"
        save_gcode_to_file(gcode, filename)
        preview_window.title(f"Preview {filename}")
        preview_window.geometry("400x600")

        # Text widget with both vertical and horizontal scrollbars
        text_frame = ttk.Frame(preview_window, padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap=tk.NONE, height=20, width=50)
        text_widget.grid(row=0, column=0, sticky=(tk.W + tk.E + tk.N + tk.S))

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N + tk.S))
        text_widget.configure(yscrollcommand=v_scrollbar.set)

        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W + tk.E))
        text_widget.configure(xscrollcommand=h_scrollbar.set)

        # Insert G-code
        for line in gcode:
            text_widget.insert(tk.END, line + "\n")
        text_widget.config(state=tk.DISABLED)

        # Configure grid weights for resizing
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)


if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeGeneratorGUI(root)
    root.mainloop()
