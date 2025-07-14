#!/usr/bin/env python3
"""
启动Gateway和API服务器的脚本
使用uvicorn启动两个FastAPI应用
"""

import multiprocessing
import os
import sys
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
    # 不注册信号处理器，让子进程自己处理信号

    # 配置参数
    api_host = "127.0.0.1"
    api_port = 8000
    gateway_host = "127.0.0.1"
    gateway_port = 8001
    reload_mode = "--reload" in sys.argv or "-r" in sys.argv
    dev_mode = "--dev" in sys.argv

    # 设置日志级别
    log_level = "debug" if dev_mode else "info"

    # 设置应用程序日志级别环境变量
    os.environ["LOG_LEVEL"] = log_level.upper()

    print("=" * 60)
    print("🎯 MyUnla 服务器启动器")
    print("=" * 60)
    print(f"📡 API服务器地址: http://{api_host}:{api_port}")
    print(f"🌐 Gateway服务器地址: http://{gateway_host}:{gateway_port}")
    print(f"🔄 热重载模式: {'启用' if reload_mode else '禁用'}")
    print(f"🐛 开发模式: {'启用' if dev_mode else '禁用'}")
    print(f"📝 日志级别: {log_level.upper()}")
    print("=" * 60)

    api_process = None
    gateway_process = None

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

        # 等待进程完成，使用更长的睡眠间隔减少CPU使用
        try:
            while (api_process and api_process.is_alive()) or (
                gateway_process and gateway_process.is_alive()
            ):
                time.sleep(1.0)  # 增加睡眠时间，减少CPU使用
        except KeyboardInterrupt:
            # 优雅地处理键盘中断
            pass

    except KeyboardInterrupt:
        print("\n⚠️  收到中断信号，正在关闭服务器...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
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
                    process.join(timeout=10)  # 增加超时时间到10秒
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
