class Platform :

    @staticmethod
    def detect_board() -> str:
        """
        Detects and returns the Raspberry Pi board model as a string.
        """
        try:
            with open('/proc/device-tree/model') as f:
                model = f.read().strip()  # Read and remove leading/trailing whitespace
                return model
        except FileNotFoundError:
            return "Raspberry Pi model file not found."
        except Exception as e:
            return f"An error occurred: {e}"