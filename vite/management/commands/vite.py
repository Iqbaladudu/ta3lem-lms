import os.path
import subprocess
import threading

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from vite import NpmManager


class Command(BaseCommand):
    help = "Vite management command"

    @staticmethod
    def get_app_cwd(app_name):
        app_config = apps.get_app_config(app_name)
        app_path = app_config.path
        return os.path.abspath(app_path)

    def add_arguments(self, parser):
        parser.add_argument('package_name', type=str, help='NPM package name to install')

    def handle(self, *args, **options):
        print(options)
        subcommand = options.get("package_name")

        if subcommand == "dev":
            self.handle_dev()
        else:
            self.stdout.write(self.style.ERROR(f"Unknown subcommand: {subcommand}"))

    def stream_output(self, process, prefix, style_func=None):
        """Thread function untuk membaca output dari proses"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    if style_func:
                        self.stdout.write(style_func(f"{prefix}: {line.strip()}"))
                    else:
                        self.stdout.write(f"{prefix}: {line.strip()}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"{prefix} error: {e}"))

    def stream_error(self, process, prefix):
        """Thread function untuk membaca error output dari proses"""
        try:
            for line in iter(process.stderr.readline, ''):
                if line:
                    self.stdout.write(self.style.WARNING(f"{prefix} [ERROR]: {line.strip()}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"{prefix} stderr error: {e}"))

    def handle_dev(self):
        vite_dir = self.get_app_cwd(app_name="vite")
        django_dir = settings.BASE_DIR
        vite_server = NpmManager(cwd=f'{vite_dir}/src')

        if vite_server.is_npm_installed():
            vite_process = vite_server.npm_run_dev()

            if not vite_process:
                self.stdout.write(self.style.ERROR('Failed to start Vite server'))
                return

            django_process = subprocess.Popen(
                ["uv", "run", "manage.py", "runserver"],
                cwd=django_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Buat thread untuk membaca output dari kedua proses
            vite_stdout_thread = threading.Thread(
                target=self.stream_output,
                args=(vite_process, "Vite", self.style.SUCCESS),
                daemon=True
            )
            vite_stderr_thread = threading.Thread(
                target=self.stream_error,
                args=(vite_process, "Vite"),
                daemon=True
            )
            django_stdout_thread = threading.Thread(
                target=self.stream_output,
                args=(django_process, "Django", self.style.HTTP_INFO),
                daemon=True
            )
            django_stderr_thread = threading.Thread(
                target=self.stream_error,
                args=(django_process, "Django"),
                daemon=True
            )

            # Start semua thread
            vite_stdout_thread.start()
            vite_stderr_thread.start()
            django_stdout_thread.start()
            django_stderr_thread.start()

            self.stdout.write(self.style.SUCCESS('\nStarting Vite and Django servers...'))
            self.stdout.write(self.style.WARNING('Press Ctrl+C to stop both servers.\n'))

            try:
                # Tunggu sampai salah satu proses berhenti atau user menekan Ctrl+C
                while vite_process.poll() is None and django_process.poll() is None:
                    vite_process.wait(timeout=0.1)
                    django_process.wait(timeout=0.1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n\nStopping servers...'))
            except Exception:
                pass
            finally:
                # Hentikan kedua proses
                if vite_process.poll() is None:
                    vite_process.terminate()
                    try:
                        vite_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        vite_process.kill()

                if django_process.poll() is None:
                    django_process.terminate()
                    try:
                        django_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        django_process.kill()

                self.stdout.write(self.style.SUCCESS('Servers stopped.'))
