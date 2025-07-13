#!/usr/bin/env python3
"""
启动Gateway和API服务器的脚本
使用uvicorn启动两个FastAPI应用
"""

import multiprocessing
import os
import signal
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

    print(f"🚀 启动API服务器在 http://{host}:{port}")
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

    print(f"🚀 启动Gateway服务器在 http://{host}:{port}")

    # 创建Gateway应用实例
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


def signal_handler(signum, frame):
    """信号处理器，用于优雅地关闭服务器"""
    print(f"\n⚠️  收到信号 {signum}，正在关闭服务器...")
    # 不直接退出，让主进程处理清理逻辑
    raise KeyboardInterrupt


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 配置参数
    api_host = "127.0.0.1"
    api_port = 8000
    gateway_host = "127.0.0.1"
    gateway_port = 8001
    reload_mode = "--reload" in sys.argv or "-r" in sys.argv
    dev_mode = "--dev" in sys.argv

    # 设置日志级别
    log_level = "debug" if dev_mode else "info"

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

        # 等待进程完成
        while (api_process and api_process.is_alive()) or (
            gateway_process and gateway_process.is_alive()
        ):
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n⚠️  收到中断信号，正在关闭服务器...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # 确保进程被清理
        if api_process and api_process.is_alive():
            print("🔄 正在停止API服务器...")
            api_process.terminate()
            api_process.join(timeout=5)
            if api_process.is_alive():
                api_process.kill()

        if gateway_process and gateway_process.is_alive():
            print("🔄 正在停止Gateway服务器...")
            gateway_process.terminate()
            gateway_process.join(timeout=5)
            if gateway_process.is_alive():
                gateway_process.kill()

        print("✅ 所有服务器已停止")


if __name__ == "__main__":
    # 设置多进程启动方式（解决某些平台的兼容性问题）
    if sys.platform != "win32":
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)
    main()
