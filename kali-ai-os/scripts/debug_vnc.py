#!/usr/bin/env python3
"""
Quick VNC Debug Script
Run this to diagnose VNC issues on Kali
"""

import os
import shutil
import subprocess  # noqa: S404
import tempfile
import time


def check_vnc_dependencies() -> bool:
    """Check if VNC dependencies are available"""
    print("🔍 Checking VNC Dependencies...")

    # Check x11vnc
    try:
        x11vnc_path = shutil.which('x11vnc')
        if x11vnc_path:
            print(f"✅ x11vnc found at: {x11vnc_path}")
        else:
            print("❌ x11vnc not found")
            return False
    except Exception as e:
        print(f"❌ Error checking x11vnc: {e}")
        return False

    # Check Xvfb
    try:
        xvfb_path = shutil.which('Xvfb')
        if xvfb_path:
            print(f"✅ Xvfb found at: {xvfb_path}")
        else:
            print("❌ Xvfb not found")
            return False
    except Exception as e:
        print(f"❌ Error checking Xvfb: {e}")
        return False

    return True


def test_xvfb() -> bool:
    """Test if Xvfb can start"""
    print("\n🖥️  Testing Xvfb...")

    test_display = ':99'

    xvfb_path = shutil.which('Xvfb')
    xdpyinfo_path = shutil.which('xdpyinfo')

    if not xvfb_path:
        print("❌ Xvfb executable not found.")
        return False
    if not xdpyinfo_path:
        print("❌ xdpyinfo executable not found.")
        return False

    try:
        print(f"Starting Xvfb on {test_display}...")
        proc = subprocess.Popen(  # noqa: S603
            [xvfb_path, test_display, '-screen', '0', '800x600x24', '-ac'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(2)

        if proc.poll() is None:
            print(f"✅ Xvfb started successfully on {test_display}")

            # Test if display is accessible
            try:
                check = subprocess.run(  # noqa: S603
                    [xdpyinfo_path, '-display', test_display],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if check.returncode == 0:
                    print(f"✅ Display {test_display} is accessible")
                else:
                    print(f"⚠️  Display {test_display} not accessible: {check.stderr}")
            except Exception as e:
                print(f"⚠️  Cannot verify display: {e}")

            # Cleanup
            proc.terminate()
            proc.wait()
            return True
        else:
            stdout, stderr = proc.communicate()
            print("❌ Xvfb failed to start")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return False

    except Exception as e:
        print(f"❌ Xvfb test error: {e}")
        return False


def test_x11vnc() -> bool:
    """Test if x11vnc can start"""
    print("\n📺 Testing x11vnc...")

    test_display = ':98'

    xvfb_path = shutil.which('Xvfb')
    x11vnc_path = shutil.which('x11vnc')

    if not xvfb_path:
        print("❌ Xvfb executable not found.")
        return False
    if not x11vnc_path:
        print("❌ x11vnc executable not found.")
        return False

    # First start Xvfb
    print(f"Starting Xvfb on {test_display}...")
    xvfb_proc = subprocess.Popen(  # noqa: S603
        [xvfb_path, test_display, '-screen', '0', '800x600x24', '-ac'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)

    if xvfb_proc.poll() is not None:
        print("❌ Cannot start Xvfb for VNC test")
        return False

    try:
        # Test x11vnc without -bg to see output
        print(f"Testing x11vnc on {test_display}...")
        vnc_cmd = [
            x11vnc_path,
            '-display',
            test_display,
            '-rfbport',
            '5999',
            '-localhost',
            '-nopw',
            '-once',
            '-timeout',
            '5',
        ]

        print(f"Running: {' '.join(vnc_cmd)}")

        result = subprocess.run(vnc_cmd, capture_output=True, text=True, timeout=15)  # noqa: S603

        print(f"x11vnc return code: {result.returncode}")
        print(f"x11vnc stdout: {result.stdout}")
        print(f"x11vnc stderr: {result.stderr}")

        if result.returncode == 0:
            print("✅ x11vnc ran successfully")
            return True
        else:
            print("❌ x11vnc failed")
            return False

    except subprocess.TimeoutExpired:
        print("⚠️  x11vnc test timed out (this might be normal)")
        return True
    except Exception as e:
        print(f"❌ x11vnc test error: {e}")
        return False
    finally:
        # Cleanup
        xvfb_proc.terminate()
        xvfb_proc.wait()


def check_permissions() -> None:
    """Check permissions and environment"""
    print("\n🔐 Checking Permissions...")

    # Check if running as root
    if os.geteuid() == 0:
        print("⚠️  Running as root - VNC might have issues")
    else:
        print(f"✅ Running as user: {os.getenv('USER', 'unknown')}")

    # Check DISPLAY
    display = os.getenv('DISPLAY')
    if display:
        print(f"✅ DISPLAY set to: {display}")
    else:
        print("⚠️  No DISPLAY environment variable")

    # Check tmp permissions
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_file")
            with open(test_file, "w") as f:
                f.write("test")
            print("✅ /tmp (or system temp) is writable")
    except Exception as e:
        print(f"❌ /tmp (or system temp) is not writable: {e}")


def main() -> None:
    print("🚀 VNC Debug Script for Kali VM")
    print("=" * 40)

    # Check dependencies
    if not check_vnc_dependencies():
        print("\n❌ Missing dependencies - install with:")
        print("sudo apt update && sudo apt install -y x11vnc xvfb")
        return

    # Check permissions
    check_permissions()

    # Test Xvfb
    if not test_xvfb():
        print("\n❌ Xvfb test failed")
        return

    # Test x11vnc
    if not test_x11vnc():
        print("\n❌ x11vnc test failed")
        return

    print("\n✅ All VNC tests passed!")
    print("The VNC system should work. If the main test still fails,")
    print("check the VNC server implementation for issues.")


if __name__ == "__main__":
    main()
