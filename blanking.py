import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

# Updated material database with single-value parameters
CUTTING_PARAMETER = {
    "SS400": {
        "feed_rate": [1200.0],  # mm/min
        "spindle_speed": [1500],  # RPM
        "depth_of_cut": [0.75],  # mm
    },
    "S45C": {
        "feed_rate": [1000.0],
        "spindle_speed": [1500],
        "depth_of_cut": [0.5],
    },
    "DC11": {
        "feed_rate": [800.0],
        "spindle_speed": [1200],
        "depth_of_cut": [0.3],
    },
}


def tool_back(code, z_init_post, safe_tool_distance, tool_diameter, workpiece_thickness):
    code.append("G00 Z{:.2f}".format(z_init_post))  # Move to safe height
    code.append(
        "G00 X{:.2f} Y{:.2f}".format(-safe_tool_distance - (tool_diameter / 2), -workpiece_thickness / 2)
    )  # Move to starting position (slightly before material)


def start_coolant(code):
    code.append("M08")


def stop_coolant(code):
    code.append("M09")


def tool_offset(code, z_height):
    code.append("G43 H04 Z{}".format(z_height))


def pause_process(code, spindle_speed):
    code.append("M00")  # Program stop
    code.append("M03 S{}".format(spindle_speed))  # Spindle on after resume


def debug_message(message, just_clean_depth, remaining_stock, num_passes):
    print("{} Cut".format(message))
    print("Just clean depth: {:.2f} mm".format(just_clean_depth))
    print("Remaining stock: {:.2f} mm".format(remaining_stock))
    print("Number of adjustment passes: {}".format(num_passes))


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
    workpiece_long=100.0,
    workpiece_short=50.0,
    workpiece_thick=20.0,
    parallel_block_long=0.0,
    parallel_block_short=0.0,
    long_stock_thickness=155.0,
    short_stock_thickness=53.0,
    tool_diameter=63.0,
    feed_rate=500.0,
    spindle_speed=2000,
    depth_of_cut=1.0,
    safe_z_distance=20.0,
    safe_tool_distance=5.0,
    just_clean_fraction=0.1,
    debug=False,
):
    z_long_init = workpiece_short + safe_z_distance + parallel_block_long
    total_stock_long = short_stock_thickness - workpiece_short
    num_passes_long = int(total_stock_long / depth_of_cut) + (1 if total_stock_long % depth_of_cut > 0 else 0)
    passes_per_side_long = num_passes_long // 2 + (1 if num_passes_long % 2 == 1 else 0)

    if debug:
        print("Long Side Adjustment")
        print("Total stock to remove: {:.2f} mm".format(total_stock_long))
        print("Total number of passes: {}".format(num_passes_long))
        print(
            "Passes per side: {} (first side), {} (second side)".format(
                passes_per_side_long, num_passes_long - passes_per_side_long
            )
        )

    gcode = []
    gcode.append("%")
    gcode.append("O0131")
    gcode.append("G00 G40 G49 G80")
    gcode.append("G21 G90 G54")
    tool_zero_return(gcode, all_axis=True)
    reset_coordinate(gcode)
    gcode.append("(FACEMILL DIA. 63)")
    gcode.append("M06 T10")
    gcode.append("M03 S{}".format(int(spindle_speed)))
    tool_offset(gcode, z_long_init)

    direction = 1
    gcode.append("(CEKAM SISI PANJANG)")
    gcode.append("(ADJUSTMENT SISI PANJANG - SISI PERTAMA)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)

    for pass_num in range(passes_per_side_long):
        current_depth = (pass_num + 1) * depth_of_cut
        if current_depth > total_stock_long:
            current_depth = total_stock_long

        gcode.append(
            "G01 Z{:.2f} F{:.1f}".format(short_stock_thickness + parallel_block_long - current_depth, feed_rate / 2)
        )
        adjustment_feed_rate = feed_rate / 2 if pass_num == passes_per_side_long - 1 else feed_rate
        if direction == 1:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    workpiece_long + 5 + (tool_diameter / 2), -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = -1
        else:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    -tool_diameter / 2 - safe_tool_distance, -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = 1

    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, int(spindle_speed))
    reset_coordinate(gcode)
    tool_offset(gcode, z_long_init)

    direction = 1
    gcode.append("(PUTAR KE SISI BERLAWANAN)")
    gcode.append("(ADJUSTMENT SISI PANJANG - SISI KEDUA)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)

    for pass_num in range(passes_per_side_long, num_passes_long):
        current_depth = (pass_num + 1) * depth_of_cut
        if current_depth > total_stock_long:
            current_depth = total_stock_long

        gcode.append(
            "G01 Z{:.2f} F{:.1f}".format(short_stock_thickness + parallel_block_long - current_depth, feed_rate / 2)
        )
        adjustment_feed_rate = feed_rate / 2 if pass_num == num_passes_long - 1 else feed_rate
        if direction == 1:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    workpiece_long + 5 + (tool_diameter / 2), -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = -1
        else:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    -tool_diameter / 2 - safe_tool_distance, -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = 1

    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, int(spindle_speed))
    reset_coordinate(gcode)

    z_short_init = workpiece_long + safe_z_distance + parallel_block_long
    tool_offset(gcode, z_height=z_short_init)
    total_stock_short = long_stock_thickness - workpiece_long
    num_passes_short = int(total_stock_short / depth_of_cut) + (1 if total_stock_short % depth_of_cut > 0 else 0)
    passes_per_side_short = num_passes_short // 2 + (1 if num_passes_short % 2 == 1 else 0)

    if debug:
        print("Short Side Adjustment")
        print("Total stock to remove: {:.2f} mm".format(total_stock_short))
        print("Total number of passes: {}".format(num_passes_short))
        print(
            "Passes per side: {} (first side), {} (second side)".format(
                passes_per_side_short, num_passes_short - passes_per_side_short
            )
        )

    direction = 1
    gcode.append("(CEKAM SISI PENDEK)")
    gcode.append("(ADJUSTMENT SISI PENDEK - SISI PERTAMA)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)

    for pass_num in range(passes_per_side_short):
        current_depth = (pass_num + 1) * depth_of_cut
        if current_depth > total_stock_short:
            current_depth = total_stock_short

        gcode.append(
            "G01 Z{:.2f} F{:.1f}".format(long_stock_thickness + parallel_block_short - current_depth, feed_rate / 2)
        )
        adjustment_feed_rate = feed_rate / 2 if pass_num == passes_per_side_short - 1 else feed_rate
        if direction == 1:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    workpiece_short + 5 + (tool_diameter / 2), -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = -1
        else:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    -tool_diameter / 2 - safe_tool_distance, -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = 1

    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, int(spindle_speed))
    reset_coordinate(gcode)
    tool_offset(gcode, z_short_init)

    direction = 1
    gcode.append("(PUTAR KE SISI BERLAWANAN)")
    gcode.append("(ADJUSTMENT SISI PENDEK - SISI KEDUA)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)

    for pass_num in range(passes_per_side_short, num_passes_short):
        current_depth = (pass_num + 1) * depth_of_cut
        if current_depth > total_stock_short:
            current_depth = total_stock_short

        gcode.append(
            "G01 Z{:.2f} F{:.1f}".format(long_stock_thickness + parallel_block_short - current_depth, feed_rate / 2)
        )
        adjustment_feed_rate = feed_rate / 2 if pass_num == num_passes_short - 1 else feed_rate
        if direction == 1:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    workpiece_short + 5 + (tool_diameter / 2), -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = -1
        else:
            gcode.append(
                "G01 X{:.2f} Y{:.2f} F{:.1f}".format(
                    -tool_diameter / 2 - safe_tool_distance, -workpiece_thick / 2, adjustment_feed_rate
                )
            )
            direction = 1

    stop_coolant(gcode)
    tool_spindle_stop(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    gcode.append("M30")
    gcode.append("%")

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
        self.root.geometry("300x450")  # Restored height for material selection

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

        # Parameters and their default values (aligned with SS400)
        self.parameters = {
            "workpiece_long": [150.0, "Panjang Blank"],
            "workpiece_short": [50.0, "Lebar Blank"],
            "workpiece_thick": [20.0, "Tebal Blank"],
            "parallel_block_long": [0.0, "Parallel Block Panjang"],
            "parallel_block_short": [0.0, "Parallel Block Pendek"],
            "long_stock_thickness": [155.0, "Panjang Aktual"],
            "short_stock_thickness": [55.0, "Lebar Aktual"],
            "tool_diameter": [63.0, "Diameter Tool"],
            "feed_rate": [1200.0, "Feed Rate"],  # SS400 default
            "spindle_speed": [1500.0, "Kecepatan Spindle"],  # SS400 default
            "depth_of_cut": [0.75, "Depth of Cut"],  # SS400 default
            "safe_z_distance": [50.0, "Safe Z Distance"],
            "safe_tool_distance": [5.0, "Safe X Distance"],
            "just_clean_fraction": [0.1, "Just Clean Fraction"],
            "debug": False,
        }

        # Split parameters into two groups
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

        # Entries and Comboboxes dictionary
        self.entries = {}

        # Workpiece Settings Tab
        row = 0
        # Material Selection
        ttk.Label(workpiece_frame, text="Material", width=20, anchor="e").grid(row=row, column=0, pady=2, padx=2)
        self.material_var = tk.StringVar(value="SS400")
        material_combo = ttk.Combobox(
            workpiece_frame,
            textvariable=self.material_var,
            values=list(CUTTING_PARAMETER.keys()),
            state="readonly",
            width=10,
        )
        material_combo.grid(row=row, column=1, sticky=(tk.W + tk.E), pady=2)
        material_combo.bind("<<ComboboxSelected>>", self.update_material_params)
        row += 1

        for param in workpiece_params:
            label_text = self.parameters[param][1]
            ttk.Label(workpiece_frame, text="{}".format(label_text), width=20, anchor="e").grid(
                row=row, column=0, pady=2, padx=2
            )
            self.entries[param] = ttk.Entry(workpiece_frame, width=10)
            self.entries[param].grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            self.entries[param].insert(0, str(self.parameters[param][0]))

            units = "mm" if "fraction" not in param else "%"
            ttk.Label(workpiece_frame, text=units, width=10).grid(row=row, column=2, sticky=tk.W, pady=2)
            row += 1

        # Tool Settings Tab
        row = 0
        for param in tool_params:
            label_text = self.parameters[param][1]
            ttk.Label(tool_frame, text="{}".format(label_text), width=20, anchor="e").grid(
                row=row, column=0, pady=2, padx=2
            )

            if param in ["feed_rate", "spindle_speed", "depth_of_cut"]:
                # Use Combobox for these parameters
                self.entries[param] = ttk.Combobox(tool_frame, width=10, state="readonly")
                self.update_combo_values(param, "SS400")  # Initialize with SS400
            else:
                # Use Entry for other parameters
                self.entries[param] = ttk.Entry(tool_frame, width=10)
                self.entries[param].insert(0, str(self.parameters[param][0]))

            self.entries[param].grid(row=row, column=1, sticky=(tk.W + tk.E), pady=2)

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

        # Filename entry
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

    def update_combo_values(self, param, material):
        """Update Combobox values based on selected material"""
        values = CUTTING_PARAMETER[material][param]
        self.entries[param]["values"] = values
        self.entries[param].set(str(values[0]))  # Set to the single value

    def update_material_params(self, event):
        """Update all material-dependent parameters when material changes"""
        material = self.material_var.get()
        for param in ["feed_rate", "spindle_speed", "depth_of_cut"]:
            self.update_combo_values(param, material)

    def validate_number_input(self, value, param_name):
        """Validate that the input is a number using '.' for decimal point and no ','"""
        if "," in value:
            return False, "{} contains a comma. Please use a decimal point (.).".format(param_name)
        if not re.match(r"^-?\d*\.?\d*$", value):
            return False, "{} is not a valid number.".format(param_name)
        return True, ""

    def generate_gcode(self):
        try:
            # Get parameters from entries
            params = {}
            for param in self.parameters:
                if param == "debug":
                    params[param] = self.debug_var.get()
                else:
                    value_str = self.entries[param].get().strip()
                    # Validate input for decimal point and no comma
                    is_valid, error_msg = self.validate_number_input(value_str, self.parameters[param][1])
                    if not is_valid:
                        raise ValueError(error_msg)
                    # Convert to float
                    value = float(value_str)
                    # Existing validation for positive/zero values
                    if value < 0 and param[:8] == "parallel":
                        raise ValueError("{} must be positive or zero".format(param.replace("_", " ").title()))
                    elif value <= 0 and param[:8] != "parallel":
                        raise ValueError("{} must be positive and not zero".format(param.replace("_", " ").title()))
                    params[param] = value

            # Generate G-code
            gcode = generate_face_mill_gcode(**params)
            current_date = datetime.now().strftime("%Y%m%d")
            filename = self.filename_entry.get()
            if not filename.endswith(".nc"):
                filename += ".nc"
            filename = "{}_{}".format(current_date, filename)
            save_gcode_to_file(gcode, filename)

            # Show generated G-code in a new window
            self.show_gcode_window(gcode)

            self.status_label.config(text="Generated and saved to {}".format(filename))

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", "An error occurred: {}".format(str(e)))

    def show_gcode_window(self, gcode):
        # Create new window for G-code preview
        preview_window = tk.Toplevel(self.root)
        filename = self.filename_entry.get()
        current_date = datetime.now().strftime("%Y%m%d")
        if not filename.endswith(".nc"):
            filename += ".nc"
        filename = "{}_{}".format(current_date, filename)
        save_gcode_to_file(gcode, filename)
        preview_window.title("Preview {}".format(filename))
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
