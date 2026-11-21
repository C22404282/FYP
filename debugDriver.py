import subprocess




class DebugPort:
    def __init__(self):
        return
    
    def programBoard(self,elf_file):
        subprocess.run([
            "openocd",
            "-f", "interface/cmsis-dap.cfg",
            "-f", "target/rp2040.cfg",
            "-c", "adapter speed 5000",
            "-c", f"program {elf_file} verify reset exit"
        ], check=True)
    