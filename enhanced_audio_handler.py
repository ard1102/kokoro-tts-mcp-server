#!/usr/bin/env python3
"""
Pure Python Audio Handler for Kokoro TTS MCP Server
Provides cross-platform audio playback using only Python libraries
Removes all Windows-specific dependencies for reliable operation
"""

import os
import sys
import json
import time
import threading
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import subprocess
import ctypes
from ctypes import wintypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_handler")

class PurePythonAudioHandler:
    """Handle audio file operations using only cross-platform Python libraries with Windows-specific optimizations"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.is_windows = platform.system() == "Windows"
        self._audio_libraries = self._detect_available_libraries()
        self._windows_audio_devices = self._detect_windows_audio_devices() if self.is_windows else {}
        self._windows_driver_status = self._check_windows_audio_drivers() if self.is_windows else {}
        
        logger.info(f"Platform: {platform.system()}")
        logger.info(f"Available audio libraries: {list(self._audio_libraries.keys())}")
        
        if self.is_windows:
            logger.info(f"Windows audio devices detected: {len(self._windows_audio_devices)}")
            if self._windows_driver_status.get("compatible", False):
                logger.info("✅ Windows audio drivers are compatible")
            else:
                logger.warning("⚠️ Windows audio driver issues detected")
                for rec in self._windows_driver_status.get("recommendations", []):
                    logger.warning(f"💡 Recommendation: {rec}")
    
    def get_available_libraries(self):
        """Get list of available audio libraries"""
        return [lib for lib, available in self._audio_libraries.items() if available]
        
    def _detect_windows_audio_devices(self) -> Dict[str, Any]:
        """Detect Windows audio devices and validate MCI compatibility"""
        if not self.is_windows:
            return {}
        
        devices = {
            "default_device": None,
            "available_devices": [],
            "mci_compatible": False,
            "winsound_available": False
        }
        
        try:
            # Test winsound availability
            import winsound
            devices["winsound_available"] = True
            logger.info("✅ winsound available (Windows native)")
        except ImportError:
            logger.warning("❌ winsound not available")
        
        try:
            # Check for Windows audio devices using sounddevice
            import sounddevice as sd
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                if device['max_output_channels'] > 0:
                    devices["available_devices"].append({
                        "id": i,
                        "name": device['name'],
                        "channels": device['max_output_channels'],
                        "default_samplerate": device['default_samplerate']
                    })
            
            # Get default output device
            try:
                default_device = sd.query_devices(kind='output')
                devices["default_device"] = default_device['name']
                logger.info(f"✅ Default Windows audio device: {default_device['name']}")
            except Exception as e:
                logger.warning(f"⚠️ Could not get default audio device: {e}")
        
        except Exception as e:
            logger.warning(f"⚠️ Could not query Windows audio devices: {e}")
        
        # Test MCI compatibility
        try:
            # Try to access Windows MCI (Media Control Interface)
            winmm = ctypes.windll.winmm
            devices["mci_compatible"] = True
            logger.info("✅ Windows MCI interface accessible")
        except Exception as e:
            logger.warning(f"⚠️ Windows MCI interface not accessible: {e}")
        
        return devices
    
    def _detect_available_libraries(self) -> Dict[str, bool]:
        """Detect which audio libraries are available with Windows-specific validation"""
        libraries = {}
        
        # Test pygame with Windows-specific checks
        try:
            import pygame
            if self.is_windows:
                # Test pygame initialization on Windows
                try:
                    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.mixer.init()
                    pygame.mixer.quit()
                    libraries['pygame'] = True
                    logger.info("✅ pygame available and tested on Windows")
                except Exception as e:
                    libraries['pygame'] = False
                    logger.warning(f"❌ pygame failed Windows test: {e}")
            else:
                libraries['pygame'] = True
                logger.info("✅ pygame available")
        except ImportError:
            libraries['pygame'] = False
            logger.warning("❌ pygame not available")
        
        # Test sounddevice with device validation
        try:
            import sounddevice as sd
            import numpy as np
            if self.is_windows:
                # Validate Windows audio devices
                try:
                    devices = sd.query_devices()
                    output_devices = [d for d in devices if d['max_output_channels'] > 0]
                    if output_devices:
                        libraries['sounddevice'] = True
                        logger.info(f"✅ sounddevice available with {len(output_devices)} output devices")
                    else:
                        libraries['sounddevice'] = False
                        logger.warning("❌ sounddevice: no output devices found")
                except Exception as e:
                    libraries['sounddevice'] = False
                    logger.warning(f"❌ sounddevice device validation failed: {e}")
            else:
                libraries['sounddevice'] = True
                logger.info("✅ sounddevice available")
        except ImportError:
            libraries['sounddevice'] = False
            logger.warning("❌ sounddevice not available")
        
        # Test pydub
        try:
            from pydub import AudioSegment
            from pydub.playback import play
            libraries['pydub'] = True
            logger.info("✅ pydub available")
        except ImportError:
            libraries['pydub'] = False
            logger.warning("❌ pydub not available")
        
        # Test simpleaudio with Windows validation
        try:
            import simpleaudio as sa
            if self.is_windows:
                # Test simpleaudio on Windows
                try:
                    # Try to create a simple wave object to test functionality
                    test_data = b'\x00\x00' * 1000  # Simple silence
                    libraries['simpleaudio'] = True
                    logger.info("✅ simpleaudio available and tested on Windows")
                except Exception as e:
                    libraries['simpleaudio'] = False
                    logger.warning(f"❌ simpleaudio failed Windows test: {e}")
            else:
                libraries['simpleaudio'] = True
                logger.info("✅ simpleaudio available")
        except ImportError:
            libraries['simpleaudio'] = False
            logger.warning("❌ simpleaudio not available")
        
        return libraries
    
    def _check_windows_audio_drivers(self) -> Dict[str, Any]:
        """Check Windows audio driver compatibility and status"""
        if not self.is_windows:
            return {"compatible": True, "message": "Not Windows"}
        
        driver_status = {
            "compatible": False,
            "audio_service_running": False,
            "drivers_detected": [],
            "recommendations": []
        }
        
        try:
            # Check if Windows Audio service is running
            try:
                result = subprocess.run(
                    ['sc', 'query', 'AudioSrv'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if "RUNNING" in result.stdout:
                    driver_status["audio_service_running"] = True
                    logger.info("✅ Windows Audio service is running")
                else:
                    logger.warning("⚠️ Windows Audio service is not running")
                    driver_status["recommendations"].append("Start Windows Audio service")
            except Exception as e:
                logger.warning(f"⚠️ Could not check Windows Audio service: {e}")
            
            # Check for audio drivers using WMI (if available)
            try:
                result = subprocess.run(
                    ['wmic', 'sounddev', 'get', 'name,status'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # Skip header
                        if line.strip() and 'OK' in line:
                            driver_name = line.replace('OK', '').strip()
                            if driver_name:
                                driver_status["drivers_detected"].append(driver_name)
                    
                    if driver_status["drivers_detected"]:
                        logger.info(f"✅ Found {len(driver_status['drivers_detected'])} working audio drivers")
                        driver_status["compatible"] = True
                    else:
                        logger.warning("⚠️ No working audio drivers detected")
                        driver_status["recommendations"].append("Update or reinstall audio drivers")
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not check audio drivers via WMI: {e}")
                driver_status["recommendations"].append("Check audio drivers manually in Device Manager")
            
            # Test basic Windows audio functionality
            try:
                import winsound
                # Try to play a system sound (non-blocking test)
                winsound.MessageBeep(winsound.MB_OK)
                logger.info("✅ Windows system audio test successful")
                driver_status["compatible"] = True
            except Exception as e:
                logger.warning(f"⚠️ Windows system audio test failed: {e}")
                driver_status["recommendations"].append("Check Windows audio configuration")
            
            # Final compatibility assessment
            if driver_status["audio_service_running"] and (driver_status["drivers_detected"] or driver_status["compatible"]):
                driver_status["compatible"] = True
            
        except Exception as e:
            logger.error(f"❌ Windows audio driver check failed: {e}")
            driver_status["recommendations"].append("Manual audio system check required")
        
        return driver_status
    
    def _verify_audio_format(self, file_path: Path) -> Dict[str, Any]:
        """Verify and validate audio file format for Windows compatibility"""
        try:
            format_info = {
                "valid": False,
                "format": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
                "recommendations": []
            }
            
            # Check file extension
            supported_formats = {".wav", ".mp3", ".ogg", ".m4a", ".flac"}
            if format_info["format"] not in supported_formats:
                format_info["recommendations"].append(f"Unsupported format {format_info['format']}. Convert to WAV for best compatibility.")
                return format_info
            
            # Check file size (empty files cause issues)
            if format_info["size_bytes"] < 100:
                format_info["recommendations"].append("File too small, may be corrupted or empty.")
                return format_info
            
            # Try to read file header for additional validation
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(12)
                    
                if format_info["format"] == ".wav":
                    if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                        format_info["valid"] = True
                    else:
                        format_info["recommendations"].append("Invalid WAV file header.")
                elif format_info["format"] == ".mp3":
                    if header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
                        format_info["valid"] = True
                    else:
                        format_info["recommendations"].append("Invalid MP3 file header.")
                else:
                    # For other formats, assume valid if we got this far
                    format_info["valid"] = True
                    
            except Exception as e:
                format_info["recommendations"].append(f"Could not read file header: {e}")
                
            return format_info
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "recommendations": ["File validation failed"]
            }
    
    def _handle_windows_mci_error(self, error_msg: str) -> Dict[str, Any]:
        """Handle Windows MCI (Media Control Interface) errors"""
        mci_solutions = {
            "263": {
                "description": "The specified device is not open or is not recognized by MCI",
                "solutions": [
                    "Update audio drivers",
                    "Try running as administrator",
                    "Use alternative audio library (sounddevice/pygame)",
                    "Check Windows audio service is running"
                ]
            },
            "259": {
                "description": "The driver cannot recognize the specified command parameter",
                "solutions": [
                    "Convert audio to WAV format",
                    "Check audio file is not corrupted",
                    "Try different audio library"
                ]
            },
            "277": {
                "description": "The file format is invalid",
                "solutions": [
                    "Convert to WAV format",
                    "Check file is not corrupted",
                    "Use pydub for format conversion"
                ]
            }
        }
        
        # Extract error code from message
        error_code = None
        for code in mci_solutions.keys():
            if code in error_msg:
                error_code = code
                break
        
        if error_code:
            return {
                "error_type": "MCI Error",
                "error_code": error_code,
                "description": mci_solutions[error_code]["description"],
                "solutions": mci_solutions[error_code]["solutions"]
            }
        else:
            return {
                "error_type": "Unknown MCI Error",
                "description": error_msg,
                "solutions": [
                    "Try alternative audio library",
                    "Check audio drivers",
                    "Convert to WAV format"
                ]
            }
    
    def _windows_winsound_fallback(self, file_path: Path) -> Dict[str, Any]:
        """Emergency Windows fallback using winsound"""
        if not self.is_windows:
            return {"success": False, "error": "winsound only available on Windows"}
        
        try:
            import winsound
            
            # Only WAV files are supported by winsound
            if file_path.suffix.lower() != ".wav":
                return {
                    "success": False,
                    "error": "winsound only supports WAV files",
                    "recommendation": "Convert to WAV format first"
                }
            
            def winsound_play():
                try:
                    winsound.PlaySound(str(file_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                    logger.info(f"✅ winsound playback started: {file_path.name}")
                except Exception as e:
                    logger.error(f"❌ winsound playback error: {e}")
            
            thread = threading.Thread(target=winsound_play, daemon=True)
            thread.start()
            time.sleep(0.1)  # Brief pause to ensure playback starts
            
            return {
                "success": True,
                "message": f"Playing with Windows winsound (emergency fallback): {file_path.name}",
                "method": "winsound",
                "file_path": str(file_path.absolute())
            }
            
        except ImportError:
            return {"success": False, "error": "winsound not available"}
        except Exception as e:
            return {"success": False, "error": f"winsound error: {e}"}
    
    def play_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Play audio file using pure Python libraries with Windows-specific optimizations"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            
            logger.info(f"🔊 Attempting to play: {file_path.name}")
            
            # Windows-specific pre-flight checks
            if self.is_windows:
                # Verify audio format
                format_check = self._verify_audio_format(file_path)
                if not format_check["valid"]:
                    logger.warning(f"⚠️ Audio format validation failed: {format_check.get('recommendations', [])}")
                    # Continue anyway, but log the warning
                
                # Check if we have any working audio devices
                if not self._windows_audio_devices.get("available_devices") and not self._windows_audio_devices.get("winsound_available"):
                    return {
                        "success": False,
                        "error": "No Windows audio devices detected",
                        "recommendations": [
                            "Check audio drivers are installed",
                            "Verify Windows audio service is running",
                            "Try running as administrator"
                        ]
                    }
            
            # Method 1: sounddevice + numpy (most reliable for cross-platform)
            if self._audio_libraries.get('sounddevice', False):
                try:
                    import sounddevice as sd
                    import numpy as np
                    from scipy.io import wavfile
                    
                    # Read WAV file
                    sample_rate, audio_data = wavfile.read(str(file_path))
                    
                    # Ensure audio data is in the right format
                    original_dtype = audio_data.dtype
                    if original_dtype != np.float32:
                        if original_dtype == np.int16:
                            audio_data = audio_data.astype(np.float32) / 32768.0
                        elif original_dtype == np.int32:
                            audio_data = audio_data.astype(np.float32) / 2147483648.0
                        else:
                            audio_data = audio_data.astype(np.float32)
                    
                    # Play audio in a separate thread
                    def sounddevice_play():
                        try:
                            sd.play(audio_data, sample_rate)
                            sd.wait()  # Wait until playback is finished
                            logger.info(f"✅ sounddevice playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ sounddevice playback error: {e}")
                    
                    thread = threading.Thread(target=sounddevice_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ sounddevice playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with sounddevice: {file_path.name}",
                        "method": "sounddevice",
                        "file_path": str(file_path.absolute()),
                        "sample_rate": int(sample_rate),
                        "duration_seconds": len(audio_data) / sample_rate
                    }
                    
                except ImportError:
                    logger.warning("⚠️ scipy not available for sounddevice, trying next method")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ sounddevice error: {error_msg}")
                    
                    # Windows-specific error handling
                    if self.is_windows and ("263" in error_msg or "MCI" in error_msg or "device" in error_msg.lower()):
                        mci_info = self._handle_windows_mci_error(error_msg)
                        logger.warning(f"🔧 Windows MCI issue detected: {mci_info['description']}")
                        logger.info(f"💡 Suggested solutions: {mci_info['solutions']}")
            
            # Method 2: pygame (reliable and cross-platform)
            if self._audio_libraries.get('pygame', False):
                try:
                    import pygame
                    
                    # Initialize pygame mixer if not already done
                    if not pygame.mixer.get_init():
                        pygame.mixer.pre_init(
                            frequency=44100,
                            size=-16,
                            channels=2,
                            buffer=1024
                        )
                        pygame.mixer.init()
                    
                    def pygame_play():
                        try:
                            pygame.mixer.music.load(str(file_path))
                            pygame.mixer.music.set_volume(1.0)
                            pygame.mixer.music.play()
                            
                            # Wait for playback to complete
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)
                            
                            logger.info(f"✅ pygame playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ pygame playback error: {e}")
                    
                    thread = threading.Thread(target=pygame_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ pygame playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with pygame: {file_path.name}",
                        "method": "pygame",
                        "file_path": str(file_path.absolute())
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ pygame error: {error_msg}")
                    
                    # Windows-specific error handling
                    if self.is_windows and ("263" in error_msg or "MCI" in error_msg or "mixer" in error_msg.lower()):
                        mci_info = self._handle_windows_mci_error(error_msg)
                        logger.warning(f"🔧 Windows audio issue detected: {mci_info['description']}")
            
            # Method 3: simpleaudio (lightweight and reliable)
            if self._audio_libraries.get('simpleaudio', False):
                try:
                    import simpleaudio as sa
                    
                    def simpleaudio_play():
                        try:
                            wave_obj = sa.WaveObject.from_wave_file(str(file_path))
                            play_obj = wave_obj.play()
                            play_obj.wait_done()  # Wait until playback is finished
                            logger.info(f"✅ simpleaudio playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ simpleaudio playback error: {e}")
                    
                    thread = threading.Thread(target=simpleaudio_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ simpleaudio playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with simpleaudio: {file_path.name}",
                        "method": "simpleaudio",
                        "file_path": str(file_path.absolute())
                    }
                    
                except Exception as e:
                    logger.error(f"❌ simpleaudio error: {e}")
            
            # Method 4: pydub (with fallback playback)
            if self._audio_libraries.get('pydub', False):
                try:
                    from pydub import AudioSegment
                    from pydub.playback import play
                    
                    def pydub_play():
                        try:
                            audio = AudioSegment.from_file(str(file_path))
                            # Boost volume slightly for better audibility
                            audio = audio + 5  # +5dB
                            play(audio)
                            logger.info(f"✅ pydub playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ pydub playback error: {e}")
                    
                    thread = threading.Thread(target=pydub_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ pydub playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with pydub: {file_path.name}",
                        "method": "pydub",
                        "file_path": str(file_path.absolute())
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ pydub error: {error_msg}")
                    
                    # Windows-specific error handling
                    if self.is_windows and ("263" in error_msg or "MCI" in error_msg):
                        mci_info = self._handle_windows_mci_error(error_msg)
                        logger.warning(f"🔧 Windows MCI issue detected: {mci_info['description']}")
            
            # Windows Emergency Fallback: winsound
            if self.is_windows and self._windows_audio_devices.get("winsound_available", False):
                logger.info("🆘 Trying Windows winsound emergency fallback...")
                winsound_result = self._windows_winsound_fallback(file_path)
                if winsound_result["success"]:
                    return winsound_result
                else:
                    logger.warning(f"⚠️ winsound fallback failed: {winsound_result.get('error')}")
            
            # If all methods fail
            logger.error(f"❌ All audio libraries failed for: {file_path.name}")
            
            # Enhanced error response with Windows-specific recommendations
            error_response = {
                "success": False,
                "error": "All audio playback methods failed",
                "file_path": str(file_path.absolute()),
                "available_libraries": self._audio_libraries,
                "recommendations": [
                    "Install missing audio libraries: pip install pygame sounddevice pydub simpleaudio scipy",
                    "Check if audio file format is supported (WAV recommended)",
                    "Verify system audio is working with other applications"
                ]
            }
            
            # Add Windows-specific recommendations
            if self.is_windows:
                error_response["windows_devices"] = self._windows_audio_devices
                error_response["recommendations"].extend([
                    "Try running as administrator",
                    "Update Windows audio drivers",
                    "Check Windows Audio service is running",
                    "Convert audio file to WAV format for better compatibility",
                    "Restart Windows Audio service: services.msc -> Windows Audio -> Restart"
                ])
            
            return error_response
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in play_audio_file: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path) if 'file_path' in locals() else "unknown"
            }
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about an audio file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            stat = file_path.stat()
            info = {
                "success": True,
                "filename": file_path.name,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 2),
                "format": file_path.suffix.lower(),
                "full_path": str(file_path.absolute())
            }
            
            # Try to get additional audio info if pydub is available
            if self._audio_libraries.get('pydub', False):
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(str(file_path))
                    info.update({
                        "duration_ms": len(audio),
                        "duration_seconds": len(audio) / 1000.0,
                        "channels": audio.channels,
                        "sample_rate": audio.frame_rate,
                        "sample_width": audio.sample_width
                    })
                except Exception as e:
                    logger.warning(f"Could not get detailed audio info: {e}")
            
            return info
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_audio_files(self) -> Dict[str, Any]:
        """List all audio files in the output directory"""
        try:
            audio_extensions = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
            audio_files = []
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                    stat = file_path.stat()
                    audio_files.append({
                        "filename": file_path.name,
                        "size_kb": round(stat.st_size / 1024, 2),
                        "format": file_path.suffix.lower(),
                        "full_path": str(file_path.absolute()),
                        "modified_time": stat.st_mtime
                    })
            
            # Sort by modification time (newest first)
            audio_files.sort(key=lambda x: x["modified_time"], reverse=True)
            
            return {
                "success": True,
                "count": len(audio_files),
                "files": audio_files,
                "output_directory": str(self.output_dir.absolute())
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_audio_system(self) -> Dict[str, Any]:
        """Test the audio system to verify it's working"""
        try:
            results = {
                "success": True,
                "library_tests": {},
                "recommendations": []
            }
            
            # Test each available library
            for lib_name, available in self._audio_libraries.items():
                if available:
                    try:
                        if lib_name == "pygame":
                            import pygame
                            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
                            pygame.mixer.init()
                            results["library_tests"][lib_name] = "✅ Initialized successfully"
                            pygame.mixer.quit()
                        
                        elif lib_name == "sounddevice":
                            import sounddevice as sd
                            devices = sd.query_devices()
                            results["library_tests"][lib_name] = f"✅ Found {len(devices)} audio devices"
                        
                        elif lib_name == "pydub":
                            from pydub import AudioSegment
                            results["library_tests"][lib_name] = "✅ Available for audio processing"
                        
                        elif lib_name == "simpleaudio":
                            import simpleaudio as sa
                            results["library_tests"][lib_name] = "✅ Available for WAV playback"
                            
                    except Exception as e:
                        results["library_tests"][lib_name] = f"❌ Error: {e}"
                        results["success"] = False
                else:
                    results["library_tests"][lib_name] = "❌ Not installed"
            
            # Add recommendations based on test results
            if not any(self._audio_libraries.values()):
                results["recommendations"].append("Install audio libraries: pip install pygame sounddevice pydub simpleaudio scipy")
                results["success"] = False
            
            if not self._audio_libraries.get('sounddevice', False):
                results["recommendations"].append("Install sounddevice for best cross-platform support: pip install sounddevice scipy")
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendations": ["Check Python environment and audio library installations"]
            }

# Backward compatibility - create an alias
AudioHandler = PurePythonAudioHandler

def main():
    """Command line interface for audio handler"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pure Python Audio Handler")
    parser.add_argument("action", choices=["play", "info", "list", "test"], 
                       help="Action to perform")
    parser.add_argument("--file", "-f", help="Audio file path (for play/info actions)")
    parser.add_argument("--output-dir", "-o", default="./output", 
                       help="Output directory path")
    
    args = parser.parse_args()
    
    handler = PurePythonAudioHandler(args.output_dir)
    
    if args.action == "play":
        if not args.file:
            print("Error: --file is required for play action")
            sys.exit(1)
        result = handler.play_audio_file(args.file)
    elif args.action == "info":
        if not args.file:
            print("Error: --file is required for info action")
            sys.exit(1)
        result = handler.get_audio_info(args.file)
    elif args.action == "list":
        result = handler.list_audio_files()
    elif args.action == "test":
        result = handler.test_audio_system()
    
    print(json.dumps(result, indent=2))
    
    if not result.get("success", False):
        sys.exit(1)

if __name__ == "__main__":
    main()