import logging


def setup_logging():
    # Check if our specific handler is already added
    logger = logging.getLogger()
    
    # Look for existing console handlers to avoid duplicates
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream.name == '<stderr>':
            return  # Already set up

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "\033[35m[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    ))
    logger = logging.getLogger()
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)


class Logger:
    """
    An abstract superclass for Agents
    Used to log messages in a way that can identify each Agent
    """

    # Standard foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background color
    BG_BLACK = '\033[40m'

    # Reset code to return to default color
    RESET = '\033[0m'

    name: str = ""
    color: str = '\033[37m'

    def log(self, message, **kvargs):
        """
        Log this as an info message highlighting specific parts using keyword arguments.
        
        Args:
            message (str): Message template with placeholders in format '{key}'
            **kvargs: Keyword arguments that will be highlighted in the output
                Each value will be colored with the agent's color
        
        Example:
            logger.log("Processing {file} with {status}", file="data.txt", status="SUCCESS")
            logger.log("Request from {ip} received", ip="192.168.1.1")
        """
        color_code = self.BG_BLACK + self.color
        message_color = self.BG_BLACK + self.WHITE

        # Create a dict with colored values
        colored_args = {k: f"{color_code}{v}{message_color}" for k, v in kvargs.items()}
        
        # Format the message first
        formatted_message = message.format(**colored_args)
        
        # Add the agent name prefix
        final_message = f"[{self.name}] {message_color}{formatted_message}"
        
        logging.info(color_code + final_message + self.RESET)

    def log_hist(self, message):
        """
        Log this as a LLM message, identifying the agent
        """
        color_code = self.BG_BLACK + self.color
        message_color = self.BG_BLACK + self.YELLOW
        message = f"[{self.name}]\n{message_color}{message}"
        logging.info(color_code + message + self.RESET + "\n")


setup_logging()

if __name__ == "__main__":

    logger = Logger()
    logger.name = "Test logger"

    def test(color):
        logger.color = color
        logger.log("init...")
        logger.log("GENERATE ({i})", i="iteration 1")
        logger.log_hist("=====================\n\nhello")
        logger.log_hist("=====================\n\nhi\n")

    test(Logger.BLUE)
    test(Logger.MAGENTA)
    test(Logger.GREEN)
    test(Logger.YELLOW)
    test(Logger.RED)
    test(Logger.WHITE)
    test(Logger.CYAN)

