#!/usr/bin/env python3
"""
启动Gateway和API服务器的脚本
使用uvicorn启动两个FastAPI应用
"""

import argparse
import multiprocessing
import os
import signal
import sys
import threading
import time

import uvicorn


def start_api_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info",
):
    """启动API服务器"""
    # 设置Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    os.environ["CREATE_DEFAULT_DATA"] = "True"
    # 设置应用程序日志级别
    os.environ["LOG_LEVEL"] = log_level.upper()

    print(f"🚀 启动API服务器在 http://{host}:{port}")

    try:
        config = uvicorn.Config(
            "myunla.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
        )
        server = uvicorn.Server(config)
        server.run()

    except (KeyboardInterrupt, SystemExit):
        print("📡 API服务器正在关闭...")
    except Exception as e:
        # 捕获其他异常，包括 CancelledError 和导入错误
        import asyncio

        if isinstance(e, asyncio.CancelledError):
            print("📡 API服务器任务已取消，正在关闭...")
        else:
            print(f"📡 API服务器启动或关闭时发生错误: {e}")
    finally:
        print("📡 API服务器已停止")


def start_gateway_server(
    host: str = "127.0.0.1",
    port: int = 8001,
    reload: bool = False,
    log_level: str = "info",
):
    """启动Gateway服务器"""
    # 设置Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # 设置应用程序日志级别
    os.environ["LOG_LEVEL"] = log_level.upper()

    print(f"🚀 启动Gateway服务器在 http://{host}:{port}")

    try:
        # 在受保护的块中导入模块，避免导入期间的键盘中断
        from myunla.config import gateway_settings
        from myunla.gateway.server import GatewayServer
        from myunla.gateway.state import Metrics, State

        gateway_server = GatewayServer(
            State(
                mcps=[],
                runtime={},
                metrics=Metrics(),
            ),
            gateway_settings["session_config"],
        )

        # 初始化网关状态
        import asyncio

        async def init_gateway_state():
            await gateway_server.initialize_state()

        # 运行初始化
        asyncio.run(init_gateway_state())

        config = uvicorn.Config(
            gateway_server.app,
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
        )
        server = uvicorn.Server(config)
        server.run()

    except (KeyboardInterrupt, SystemExit):
        print("🌐 Gateway服务器正在关闭...")
    except Exception as e:
        # 捕获其他异常，包括 CancelledError 和导入错误
        import asyncio

        if isinstance(e, asyncio.CancelledError):
            print("🌐 Gateway服务器任务已取消，正在关闭...")
        else:
            print(f"🌐 Gateway服务器启动或关闭时发生错误: {e}")
    finally:
        print("🌐 Gateway服务器已停止")


def main():
    """主函数"""
    # 设置参数解析器
    parser = argparse.ArgumentParser(
        description="启动 MyUnla 的 Gateway 和 API 服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 使用默认设置启动
  %(prog)s --reload --dev     # 启用热重载和开发模式
  %(prog)s --api-port 9000    # 自定义API端口
  %(prog)s --gateway-host 0.0.0.0 --gateway-port 9001  # 自定义Gateway地址
        """,
    )

    # API服务器配置
    parser.add_argument(
        "--api-host",
        default="127.0.0.1",
        help="API服务器主机地址 (默认: 127.0.0.1)",
    )
    parser.add_argument(
        "--api-port", type=int, default=8000, help="API服务器端口 (默认: 8000)"
    )

    # Gateway服务器配置
    parser.add_argument(
        "--gateway-host",
        default="127.0.0.1",
        help="Gateway服务器主机地址 (默认: 127.0.0.1)",
    )
    parser.add_argument(
        "--gateway-port",
        type=int,
        default=8001,
        help="Gateway服务器端口 (默认: 8001)",
    )

    # 运行模式
    parser.add_argument(
        "-r", "--reload", action="store_true", help="启用热重载模式"
    )
    parser.add_argument(
        "--dev", action="store_true", help="启用开发模式 (设置日志级别为debug)"
    )

    # 日志级别
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="设置日志级别 (默认: info)",
    )

    args = parser.parse_args()

    # 使用解析的参数
    api_host = args.api_host
    api_port = args.api_port
    gateway_host = args.gateway_host
    gateway_port = args.gateway_port
    reload_mode = args.reload

    # 如果启用开发模式，强制使用debug日志级别
    log_level = "debug" if args.dev else args.log_level

    # 设置应用程序日志级别环境变量
    os.environ["LOG_LEVEL"] = log_level.upper()

    print("=" * 60)
    print("🎯 MyUnla 服务器启动器")
    print("=" * 60)
    print(f"📡 API服务器地址: http://{api_host}:{api_port}")
    print(f"🌐 Gateway服务器地址: http://{gateway_host}:{gateway_port}")
    print(f"🔄 热重载模式: {'启用' if reload_mode else '禁用'}")
    print(f"🐛 开发模式: {'启用' if args.dev else '禁用'}")
    print(f"📝 日志级别: {log_level.upper()}")
    print("=" * 60)

    # 用于跟踪进程和关闭状态的全局变量
    api_process = None
    gateway_process = None
    shutdown_event = threading.Event()

    def signal_handler(signum, _frame):
        """处理SIGINT和SIGTERM信号的处理器"""
        signal_name = 'SIGINT' if signum == signal.SIGINT else 'SIGTERM'
        print(f"\n⚠️  收到{signal_name}信号，正在关闭服务器...")
        shutdown_event.set()

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 创建并启动进程
        api_process = multiprocessing.Process(
            target=start_api_server,
            args=(api_host, api_port, reload_mode, log_level),
            name="api-server",
        )

        gateway_process = multiprocessing.Process(
            target=start_gateway_server,
            args=(gateway_host, gateway_port, reload_mode, log_level),
            name="gateway-server",
        )

        # 启动进程
        print("🔄 正在启动API服务器...")
        api_process.start()
        time.sleep(2)  # 等待API服务器启动

        print("🔄 正在启动Gateway服务器...")
        gateway_process.start()
        time.sleep(1)  # 等待Gateway服务器启动

        print("✅ 所有服务器已启动!")
        print("📋 使用 Ctrl+C 来停止所有服务器")
        print()

        # 等待关闭信号
        try:
            while not shutdown_event.is_set():
                # 检查进程是否仍在运行
                if api_process and not api_process.is_alive():
                    print("⚠️  API服务器意外退出")
                    break
                if gateway_process and not gateway_process.is_alive():
                    print("⚠️  Gateway服务器意外退出")
                    break
                time.sleep(1.0)

        except KeyboardInterrupt:
            # 额外的键盘中断处理（信号处理器会优先处理）
            shutdown_event.set()

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if (
            shutdown_event.is_set()
            or (api_process and api_process.is_alive())
            or (gateway_process and gateway_process.is_alive())
        ):
            print("\n⚠️  正在关闭服务器...")

            # 优雅地关闭进程
            processes = [
                (api_process, "API服务器"),
                (gateway_process, "Gateway服务器"),
            ]

            for process, name in processes:
                if process and process.is_alive():
                    print(f"🔄 正在停止{name}...")

                    # 首先尝试优雅关闭（发送SIGTERM）
                    process.terminate()

                    # 等待进程优雅退出
                    try:
                        process.join(timeout=10)
                    except Exception as e:
                        print(f"⚠️  等待{name}退出时发生错误: {e}")

                    # 如果进程仍在运行，强制终止
                    if process.is_alive():
                        print(f"⚠️  {name}未能优雅关闭，强制终止...")
                        process.kill()
                        try:
                            process.join(timeout=2)
                        except Exception as e:
                            print(f"⚠️  强制终止{name}时发生错误: {e}")

            print("✅ 所有服务器已停止")


if __name__ == "__main__":
    # 设置多进程启动方式（解决某些平台的兼容性问题）
    if sys.platform != "win32":
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)
    main()
