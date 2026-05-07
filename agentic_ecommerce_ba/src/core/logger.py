import os
import sys
import logging
from colorama import init, Fore, Style
from dotenv import load_dotenv

load_dotenv()
init(autoreset=True)

def setup_logger(name: str) -> logging.Logger:
    """Thiết lập Cấu hình Logging cho hệ thống Agent."""
    logger = logging.getLogger(name)
    
    # Chỉ setup nếu logger chưa có handler nào để tránh log bị lặp
    if not logger.handlers:
        logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))
        
        # In ra Console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Format (Màu sắc khi debug)
        class CustomFormatter(logging.Formatter):
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            
            FORMATS = {
                logging.DEBUG: Fore.CYAN + format_str + Style.RESET_ALL,
                logging.INFO: Fore.GREEN + format_str + Style.RESET_ALL,
                logging.WARNING: Fore.YELLOW + format_str + Style.RESET_ALL,
                logging.ERROR: Fore.RED + format_str + Style.RESET_ALL,
                logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT + format_str + Style.RESET_ALL
            }
            
            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno)
                formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
                return formatter.format(record)
                
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        
    return logger
