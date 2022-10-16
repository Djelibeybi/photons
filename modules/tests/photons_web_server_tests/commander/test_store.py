# coding: spec

import asyncio
import time
import types

import pytest
import sanic
from photons_app import helpers as hp
from photons_web_server.commander import Command, RouteTransformer, Store
from photons_web_server.server import Server
from sanic.request import Request
from sanic.response import HTTPResponse as Response
from strcs import Meta

describe "Store":
    async it "makes it easy to add routes to particular methods of new instances of the command", final_future: asyncio.Future, fake_event_loop:
        made: list[tuple[Command, int]] = []

        store = Store()

        @store.command
        class C(Command):
            @classmethod
            def add_routes(kls, routes: RouteTransformer) -> None:
                routes.http(kls.route1, "route1/<one:int>")
                routes.http(kls.route2, "route2", methods=["PUT"])

            def route1(s, request: Request, one: int) -> Response | None:
                made.append((s, one))
                return sanic.text("route1")

            def route2(s, request: Request) -> Response | None:
                made.append((s, -1))
                return sanic.text("route2")

        async def setup_routes(server: Server):
            store.register_commands(server.server_stop_future, Meta(), server.app, server)

        async with pytest.helpers.WebServerRoutes(final_future, setup_routes) as srv:
            res1 = await srv.start_request("GET", "/route1/20")
            res2 = await srv.start_request("PUT", "/route2", {"command": "one"})

        assert (await res1.text()) == "route1"
        assert (await res2.text()) == "route2"

        assert made == [(pytest.helpers.IsInstance(C), 20), (pytest.helpers.IsInstance(C), -1)]
        assert made[0][0] is not made[1][0]

    async it "supports async routes", final_future: asyncio.Future, fake_event_loop:
        made: list[object] = []
        done_things = hp.create_future()

        store = Store()

        @store.command
        class C(Command):
            @classmethod
            def add_routes(kls, routes: RouteTransformer) -> None:
                routes.http(kls.route1, "route1")

            async def route1(s, request: Request) -> Response | None:
                async def things():
                    t = time.time()
                    await hp.wait_for_first_future(s.final_future)
                    made.append(time.time() - t)
                    done_things.set_result(True)

                made.append(s.server.tasks.add(things()))

                await asyncio.sleep(3)
                return sanic.text("route1")

        async def setup_routes(server: Server):
            store.register_commands(server.server_stop_future, Meta(), server.app, server)

        async with pytest.helpers.WebServerRoutes(final_future, setup_routes) as srv:
            res1 = await srv.start_request("GET", "/route1")

        assert (await res1.text()) == "route1"
        await done_things

        assert made == [pytest.helpers.IsInstance(asyncio.Task), 3]
        assert time.time() == 3.1

    async it "logs random exceptions and returns InternalServerError", final_future: asyncio.Future, fake_event_loop, caplog:
        identifier: str
        store = Store()
        error = ValueError("NUP")

        @store.command
        class C(Command):
            @classmethod
            def add_routes(kls, routes: RouteTransformer) -> None:
                routes.http(kls.route1, "route1")

            def route1(s, request: Request) -> Response | None:
                nonlocal identifier
                identifier = request.ctx.request_identifier
                raise error

        async def setup_routes(server):
            store.register_commands(server.server_stop_future, Meta(), server.app, server)

        async with pytest.helpers.WebServerRoutes(final_future, setup_routes) as srv:
            res1 = await srv.start_request("GET", "/route1")

        assert (
            await res1.text()
        ) == '{"error_code":"InternalServerError","error":"Internal Server Error"}'
        assert res1.content_type == "application/json"

        assert len(caplog.records) > 3
        record = caplog.records[-2]
        assert (
            record.message == f"{{'request_identifier': '{identifier}', 'msg': 'ValueError: NUP'}}"
        )
        assert record.name == "photons_web_server_tests.commander.test_store:C:route1"
        assert record.exc_info == (
            ValueError,
            error,
            pytest.helpers.IsInstance(types.TracebackType),
        )

    async it "is easy to log things in route", final_future: asyncio.Future, fake_event_loop, caplog:
        identifier: str
        store = Store()

        @store.command
        class C(Command):
            @classmethod
            def add_routes(kls, routes: RouteTransformer) -> None:
                routes.http(kls.route1, "route1")

            def route1(s, request: Request) -> Response | None:
                nonlocal identifier
                identifier = request.ctx.request_identifier
                s.log.info(s.lc("Hello there", one=2))
                return sanic.text("hi")

        async def setup_routes(server):
            store.register_commands(server.server_stop_future, Meta(), server.app, server)

        async with pytest.helpers.WebServerRoutes(final_future, setup_routes) as srv:
            res1 = await srv.start_request("GET", "/route1")

        assert (await res1.text()) == "hi"

        assert len(caplog.records) > 3
        record = caplog.records[-2]
        assert (
            record.message
            == f"{{'request_identifier': '{identifier}', 'msg': 'Hello there', 'one': 2}}"
        )
        assert record.name == "photons_web_server_tests.commander.test_store:C:route1"
        assert record.exc_info is None

    async it "is possible to have progress messages on a http handler", final_future: asyncio.Future, fake_event_loop, caplog:
        identifier: str
        store = Store()

        @store.command
        class C(Command):
            @classmethod
            def add_routes(kls, routes: RouteTransformer) -> None:
                routes.http(kls.route1, "route1")

            async def route1(s, request: Request) -> Response | None:
                nonlocal identifier
                identifier = request.ctx.request_identifier
                await s.progress_cb("hi", there=True)
                await s.progress_cb(ValueError("asdf"))
                return sanic.text("hi")

        async def setup_routes(server):
            store.register_commands(server.server_stop_future, Meta(), server.app, server)

        async with pytest.helpers.WebServerRoutes(final_future, setup_routes) as srv:
            res1 = await srv.start_request("GET", "/route1")

        assert (await res1.text()) == "hi"

        assert len(caplog.records) > 4
        record = caplog.records[-3]
        assert (
            record.message
            == f"{{'request_identifier': '{identifier}', 'msg': 'progress', 'info': 'hi', 'there': True}}"
        )
        assert record.name == "photons_web_server_tests.commander.test_store:C:route1"
        assert record.exc_info is None

        record = caplog.records[-2]
        assert (
            record.message
            == f"{{'request_identifier': '{identifier}', 'msg': 'progress', 'error_code': 'ValueError', 'error': 'asdf'}}"
        )
        assert record.name == "photons_web_server_tests.commander.test_store:C:route1"
        assert record.exc_info is None
