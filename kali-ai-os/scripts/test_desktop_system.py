#!/usr/bin/env python3
"""
Test Script for New Desktop Automation System
Run this to verify the dual desktop system works correctly
"""

import os
import shutil
import subprocess  # noqa: S404
import sys
import time

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_requirements() -> bool:
    """Test if required packages are installed"""
    print("🔍 Testing Requirements...")

    requirements = {
        'Xvfb': 'xvfb',
        'scrot': 'scrot',
        'xdpyinfo': 'x11-utils',
        'import (ImageMagick)': 'imagemagick',
        'x11vnc': 'x11vnc',
        'vncviewer': 'tigervnc-viewer',
    }

    missing = []

    for tool, package in requirements.items():
        try:
            # Special handling for vncviewer
            if tool == 'vncviewer':
                # Try multiple VNC clients for mouse/keyboard control
                vnc_clients = [
                    'vncviewer',
                    'xtightvncviewer',
                    'vinagre',
                    'krdc',
                    'remmina',
                    'gvncviewer',
                ]
                vnc_found = []

                for vnc_cmd in vnc_clients:
                    if shutil.which(vnc_cmd):
                        vnc_found.append(vnc_cmd)

                if vnc_found:
                    print(f"  ✅ VNC clients found: {', '.join(vnc_found)}")
                    print("     These provide mouse/keyboard control for AI display")
                else:
                    print(f"  ⚠️  No VNC clients found (install: sudo apt install {package})")
                    print("     VNC clients enable mouse/keyboard control of AI display")
            else:
                if shutil.which(tool.split()[0]):
                    print(f"  ✅ {tool} found")
                else:
                    print(f"  ❌ {tool} missing (install: sudo apt install {package})")
                    missing.append(package)
        except Exception as e:
            print(f"  ❌ {tool} check failed: {e}")
            if tool != 'vncviewer':  # VNC viewer is optional
                missing.append(package)

    if missing:
        print("\n⚠️  Install missing packages:")
        print(f"sudo apt update && sudo apt install {' '.join(set(missing))}")
        return False

    print("✅ All requirements satisfied")
    return True


def test_display_system() -> bool:
    """Test the new display system"""
    print("\n🖥️  Testing Display System...")

    try:
        import os
        import tempfile
        import time

        from src.desktop.display.virtual_display import VirtualDisplayManager

        # Create display manager
        vm = VirtualDisplayManager()

        # Test display creation
        print("  Creating AI display...")
        ai_display = vm.create_ai_display(':10')  # Use different number

        if ai_display:
            print(f"  ✅ AI display created: {ai_display}")

            # Test screenshot
            print("  Testing screenshot...")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_screenshot_file:
                screenshot_path = temp_screenshot_file.name
            success = vm.take_screenshot(ai_display, screenshot_path)

            if success and os.path.exists(screenshot_path):
                size = os.path.getsize(screenshot_path)
                print(f"  ✅ Screenshot captured: {size} bytes")
                os.remove(screenshot_path)
            else:
                print("  ❌ Screenshot failed")

            # Test application opening
            print("  Testing application opening...")
            app_success = vm.open_application(ai_display, 'xcalc')
            if app_success:
                print("  ✅ Application opened on AI display")
                time.sleep(2)  # Let app start
            else:
                print("  ⚠️  Application opening failed (normal if xcalc not installed)")

            # Cleanup
            print("  Cleaning up...")
            vm.cleanup_all_displays()
            print("  ✅ Display cleanup complete")

            return True
        else:
            print("  ❌ Failed to create AI display")
            return False

    except Exception as e:
        print(f"  ❌ Display system test failed: {e}")
        return False


def test_desktop_controller() -> bool:
    """Test the desktop controller"""
    print("\n🎮 Testing Desktop Controller...")

    try:
        import os
        import tempfile

        from src.desktop.automation.desktop_controller import DesktopController

        # Create controller
        controller = DesktopController(display=':10')

        if controller.is_initialized:
            print("  ✅ Desktop controller initialized")

            # Test status
            status = controller.get_status()
            print(f"  📊 Status: {status['initialized']}")

            # Test screenshot
            print("  Testing screenshot via controller...")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_screenshot_file:
                screenshot_path = temp_screenshot_file.name
            screenshot = controller.capture_screenshot(screenshot_path)
            if screenshot:
                print("  ✅ Controller screenshot works")
                os.remove(screenshot)
            else:
                print("  ❌ Controller screenshot failed")

            # Test application opening
            print("  Testing application opening via controller...")
            result = controller.open_application('calculator')
            if result['success']:
                print("  ✅ Application opened via controller")
            else:
                print(f"  ⚠️  Application opening failed: {result.get('error', 'Unknown')}")

            # Cleanup
            controller.cleanup()
            print("  ✅ Controller cleanup complete")

            return True
        else:
            print("  ❌ Desktop controller failed to initialize")
            return False

    except Exception as e:
        print(f"  ❌ Desktop controller test failed: {e}")
        return False


def test_isolation() -> bool:
    """Test display isolation"""
    print("\n🔒 Testing Display Isolation...")

    current_display = os.environ.get('DISPLAY', ':0')
    print(f"  Current user display: {current_display}")

    try:
        from src.desktop.display.display_controller import DisplayController

        dc = DisplayController()
        if dc.initialize(':20'):
            ai_display = dc.get_ai_display()
            user_display = dc.get_user_display()

            print(f"  AI display: {ai_display}")
            print(f"  User display: {user_display}")

            if ai_display != user_display and ai_display is not None:
                print("  ✅ Display isolation working")

                # Test context switching
                dc.switch_to_ai_display()
                env_display = os.environ.get('DISPLAY')
                if env_display == ai_display:
                    print("  ✅ Context switching to AI display works")
                else:
                    print("  ❌ Context switching failed")

                dc.switch_to_user_display()
                env_display = os.environ.get('DISPLAY')
                if env_display == user_display:
                    print("  ✅ Context switching to user display works")
                else:
                    print("  ❌ Context switching back failed")

                dc.cleanup()
                return True
            else:
                print("  ❌ Display isolation not working")
                return False
        else:
            print("  ❌ Display controller initialization failed")
            return False

    except Exception as e:
        print(f"  ❌ Isolation test failed: {e}")
        return False


def test_vnc_system() -> bool:
    """Test VNC server and viewer system on Kali VM"""
    print("\n📺 Testing VNC System...")

    try:
        from src.desktop.display.vnc_server import VNCServer
        from src.desktop.viewer.vnc_viewer import VNCViewer

        # Test VNC server
        print("  Testing VNC server...")
        vnc_server = VNCServer()

        # Check if x11vnc is available
        x11vnc_path = shutil.which('x11vnc')
        if not x11vnc_path:
            print("  ❌ x11vnc not found - install with: sudo apt install x11vnc")
            return False
        print(f"  ✅ x11vnc available at: {x11vnc_path}")

        # Try to start VNC for a test display
        test_display = ':55'  # Use high number to avoid conflicts

        # First create a test display with Xvfb
        xvfb_path = shutil.which('Xvfb')
        xdpyinfo_path = shutil.which('xdpyinfo')

        if not xvfb_path:
            print("❌ Xvfb executable not found.")
            return False
        if not xdpyinfo_path:
            print("❌ xdpyinfo executable not found.")
            return False

        print(f"  Creating test display {test_display}...")

        try:
            print(f"  Starting Xvfb on {test_display}...")
            xvfb_proc = subprocess.Popen(  # noqa: S603
                [xvfb_path, test_display, '-screen', '0', '800x600x24', '-ac'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(3)  # Give Xvfb time to start

            # Check if Xvfb started successfully
            if xvfb_proc.poll() is not None:
                stdout, stderr = xvfb_proc.communicate()
                print("  ❌ Xvfb failed to start")
                print(f"     Xvfb stdout: {stdout.decode().strip()}")
                print(f"     Xvfb stderr: {stderr.decode().strip()}")
                return False

            print(f"  ✅ Test display {test_display} created")

            # Verify display is actually available
            try:
                check_result = subprocess.run(  # noqa: S603
                    [xdpyinfo_path, '-display', test_display],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if check_result.returncode == 0:
                    print(f"  ✅ Display {test_display} is accessible")
                else:
                    print(f"  ⚠️  Display {test_display} not accessible via xdpyinfo")
                    print(f"     xdpyinfo error: {check_result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print("  ⚠️  xdpyinfo check timed out")
            except Exception as e:
                print(f"  ⚠️  Cannot verify display: {e}")

            # Test VNC server startup
            print("  Testing VNC server startup...")
            print(f"     Trying to start VNC on {test_display}:5955")

            vnc_result = vnc_server.start_vnc_for_display(test_display, port=5955)

            if vnc_result:
                print("  ✅ VNC server started successfully")

                # Test connection info
                conn_info = vnc_server.get_vnc_connection_info()
                if conn_info:
                    print(f"  ✅ VNC connection: {conn_info['host']}:{conn_info['port']}")
                else:
                    print("  ⚠️  No VNC connection info")

                # Test if VNC is actually running
                if vnc_server.is_vnc_running():
                    print("  ✅ VNC server is running and accessible")
                else:
                    print("  ⚠️  VNC server started but not accessible")

                # Test VNC viewer
                print("  Testing VNC viewer...")
                vnc_viewer = VNCViewer()

                # Test viewer initialization (don't try to actually connect in test)
                viewer_type = vnc_viewer.get_viewer_type()
                if viewer_type == "vnc":
                    print("  ✅ VNC viewer initialized correctly")
                else:
                    print("  ⚠️  VNC viewer type issue")

                # Stop VNC server
                print("  Stopping VNC server...")
                if vnc_server.stop_vnc_server():
                    print("  ✅ VNC server stopped successfully")
                else:
                    print("  ⚠️  VNC server stop had issues")

                # Cleanup test display
                xvfb_proc.terminate()
                xvfb_proc.wait(timeout=5)
                print("  ✅ Test display cleaned up")

                return True

            else:
                print("  ❌ VNC server failed to start")

                # Get VNC server status for debugging
                status = vnc_server.get_status()
                print(f"     VNC server status: {status}")

                # Try to manually run x11vnc to see what happens
                print("  🔍 Manual x11vnc test...")
                try:
                    manual_result = subprocess.run(  # noqa: S603
                        [
                            x11vnc_path,
                            '-display',
                            test_display,
                            '-rfbport',
                            '5955',
                            '-localhost',
                            '-nopw',
                            '-once',
                            '-timeout',
                            '5',
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    print(f"     Manual x11vnc return code: {manual_result.returncode}")
                    if manual_result.stdout:
                        print(f"     Manual x11vnc stdout: {manual_result.stdout[:200]}...")
                    if manual_result.stderr:
                        print(f"     Manual x11vnc stderr: {manual_result.stderr[:200]}...")

                except subprocess.TimeoutExpired:
                    print("     Manual x11vnc test timed out")
                except Exception as e:
                    print(f"     Manual x11vnc test error: {e}")

                # Cleanup
                xvfb_proc.terminate()
                xvfb_proc.wait(timeout=5)
                return False

        except subprocess.TimeoutExpired:
            print("  ❌ Xvfb startup timed out")
            try:
                xvfb_proc.kill()
            except Exception as e:
                print(f"Error killing Xvfb process: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Display creation failed: {e}")
            try:
                if 'xvfb_proc' in locals():
                    xvfb_proc.terminate()
                    xvfb_proc.wait(timeout=5)
            except Exception as e:
                print(f"Error terminating Xvfb process: {e}")
            return False

    except ImportError as e:
        print(f"  ❌ VNC components not found: {e}")
        print("  💡 Make sure all viewer dependencies are installed")
        return False
    except Exception as e:
        print(f"  ❌ VNC test failed: {e}")
        return False


def test_vnc_clients() -> bool:
    """Test VNC clients for mouse/keyboard control"""
    print("\n🖱️  Testing VNC Clients for Interactive Control...")

    try:
        vnc_clients = [
            ('vncviewer', 'TigerVNC viewer'),
            ('xtightvncviewer', 'TightVNC viewer'),
            ('vinagre', 'GNOME VNC viewer'),
            ('krdc', 'KDE remote desktop client'),
            ('remmina', 'Remote desktop client'),
            ('gvncviewer', 'GTK VNC viewer'),
        ]

        clients_found = []

        for client_cmd, client_name in vnc_clients:
            try:
                if shutil.which(client_cmd):
                    print(f"  ✅ {client_name} ({client_cmd}) found")
                    clients_found.append(client_cmd)

                    # Test if client can show help/version (basic functionality test)
                    try:
                        help_result = subprocess.run(  # noqa: S603
                            [shutil.which(client_cmd), '--help'],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if help_result.returncode in [
                            0,
                            1,
                        ]:  # Many VNC clients return 1 for --help
                            print(f"     ✅ {client_cmd} responds to commands")
                        else:
                            print(f"     ⚠️  {client_cmd} may have issues")
                    except subprocess.TimeoutExpired:
                        print(f"     ⚠️  {client_cmd} help command timed out")
                    except Exception as e:
                        print(f"     ⚠️  {client_cmd} test failed: {e}")

            except Exception as e:
                print(f"  ❌ Error testing {client_name}: {e}")

        if clients_found:
            print(f"\n  ✅ Found {len(clients_found)} VNC client(s): {', '.join(clients_found)}")
            print("     These enable mouse/keyboard control of the AI display")
            print(
                "     Click '🖱️ Launch VNC Client' button in the VNC viewer for interactive control"
            )
            return True
        else:
            print("\n  ⚠️  No VNC clients found")
            print("     Install with: sudo apt install tigervnc-viewer")
            print("     VNC clients are needed for mouse/keyboard control")
            return False

    except Exception as e:
        print(f"  ❌ VNC clients test failed: {e}")
        return False


def test_viewer_manager() -> bool:
    """Test the viewer manager system on Kali VM"""
    print("\n🎮 Testing Viewer Manager...")

    try:
        from src.desktop.viewer.viewer_manager import ViewerManager

        # Test viewer manager creation
        print("  Creating viewer manager...")
        viewer_manager = ViewerManager()
        print("  ✅ Viewer manager initialized")

        # Test status (should work without active viewers)
        status = viewer_manager.get_status()
        if isinstance(status, dict) and 'viewing' in status:
            print(f"  ✅ Manager status: {status['viewing']}")
        else:
            print("  ⚠️  Manager status method issue")

        # Test available viewers
        viewers = viewer_manager.get_available_viewers()
        if isinstance(viewers, list) and len(viewers) > 0:
            print(f"  ✅ Available viewers: {viewers}")

            # Verify expected viewers are available
            if "vnc" in viewers:
                print("  ✅ VNC viewer available")
            else:
                print("  ⚠️  Missing VNC viewer")
        else:
            print("  ⚠️  Available viewers issue")

        # Test preferred viewer setting
        original_preferred = viewer_manager.preferred_viewer
        viewer_manager.set_preferred_viewer("vnc")
        if viewer_manager.preferred_viewer == "vnc":
            print("  ✅ Preferred viewer setting works")
            viewer_manager.set_preferred_viewer(original_preferred)  # Restore
        else:
            print("  ⚠️  Preferred viewer setting issue")

        # Test is_viewing when no viewers active (should be False)
        if not viewer_manager.is_viewing():
            print("  ✅ Viewer manager inactive state detection works")
        else:
            print("  ⚠️  Viewer manager state detection issue")

        # Test widget creation (mock parent)
        print("  Testing viewer widget integration...")
        try:
            import tkinter as tk

            # Create a test tkinter root (but don't show it)
            test_root = tk.Tk()
            test_root.withdraw()  # Hide the window

            widget = viewer_manager.get_current_viewer_widget(test_root)
            if widget:
                print("  ✅ Viewer manager widget creation works")
            else:
                print("  ⚠️  Viewer manager widget creation issue")

            test_root.destroy()

        except Exception as e:
            if "DISPLAY" in str(e) or "can't open display" in str(e).lower():
                print("  ⚠️  No display available for tkinter test (running headless)")
            else:
                print(f"  ⚠️  Widget test issue: {e}")

        # Test refresh when no viewer active (should return False)
        refresh_result = viewer_manager.refresh_current_viewer()
        if not refresh_result:
            print("  ✅ Viewer manager refresh handling works")
        else:
            print("  ⚠️  Viewer manager refresh handling issue")

        # Test individual viewer access
        if hasattr(viewer_manager, 'vnc_viewer'):
            print("  ✅ VNC viewer accessible")
        else:
            print("  ⚠️  VNC viewer access issue")

        # Test cleanup
        cleanup_result = viewer_manager.cleanup()
        if cleanup_result:
            print("  ✅ Viewer manager cleanup successful")
        else:
            print("  ⚠️  Viewer manager cleanup issue")

        return True

    except ImportError as e:
        print(f"  ❌ Viewer manager components not found: {e}")
        print("  💡 Make sure all viewer dependencies are installed")
        return False
    except Exception as e:
        print(f"  ❌ Viewer manager test failed: {e}")
        return False


def test_python_packages() -> bool:
    """Test required Python packages"""
    print("\n🐍 Testing Python Packages...")

    packages = {
        'tkinter': 'GUI framework',
        'PIL': 'Image processing',
        'cv2': 'Computer vision',
        'sounddevice': 'Audio recording',
        'pyautogui': 'GUI automation',
        'psutil': 'Process monitoring',
        'pynput': 'Input monitoring',
    }

    missing = []

    for package, description in packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package} - {description}")
        except ImportError:
            print(f"  ❌ {package} missing - {description}")
            missing.append(package)

    if missing:
        print(f"\n⚠️  Missing Python packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False

    return True


def main() -> None:
    """Run all tests"""
    print("🚀 Samsung AI-OS Desktop System Test")
    print("=" * 50)

    tests = [
        ("Requirements", test_requirements),
        ("Python Packages", test_python_packages),
        ("Display System", test_display_system),
        ("Desktop Controller", test_desktop_controller),
        ("Display Isolation", test_isolation),
        ("VNC System", test_vnc_system),
        ("VNC Clients", test_vnc_clients),
        ("Viewer Manager", test_viewer_manager),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n⏹️  Test interrupted")
            break
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The new desktop system is working correctly.")
        print("\nYou can now:")
        print("  1. Run: python3 main.py")
        print("  2. Test voice commands")
        print("  3. Take AI screenshots")
        print("  4. Open applications on isolated AI display")
        print("  5. Use VNC viewer for real-time AI display streaming")
        print("  6. Click '🖱️ Launch VNC Client' for mouse/keyboard control")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        if passed == 0:
            print("💡 Make sure you're running this in the Kali VM with X11 display")


if __name__ == "__main__":
    main()
