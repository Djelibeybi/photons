from unittest import mock

import alt_pytest_asyncio
import pytest
from delfick_project.errors_pytest import assertRaises
from delfick_project.norms import Meta, sb
from photons_app.collector import Collector
from photons_app.errors import BadOption, BadTarget, ResolverNotFound, TargetNotFound
from photons_app.registers import Target
from photons_app.special import FoundSerials, HardCodedSerials
from photons_app.tasks.register import artifact_spec, reference_spec, target_spec
from photons_control.device_finder import DeviceFinder


@pytest.fixture()
def meta():
    return Meta.empty()


@pytest.fixture()
def collector():
    with alt_pytest_asyncio.Loop(new_loop=False):
        collector = Collector()
        collector.prepare(None, {})
        yield collector


class TestArtifactSpec:
    def test_it_cares_not(self, meta):
        for thing in (
            None,
            0,
            1,
            True,
            False,
            [],
            [1],
            (),
            (1,),
            {},
            {1: 1},
            set(),
            set([1]),
            lambda: 1,
            type("a", (), {}),
            type("b", (), {})(),
            sb.NotSpecified,
        ):
            assert artifact_spec().normalise(meta, thing) is thing


class TestTargetSpec:
    class TestWithoutAValue:
        class TestMandatory:
            @pytest.mark.parametrize("val", [None, "", sb.NotSpecified])
            def test_it_complains_if_nothing_was_specified_and_is_mandatory(self, val):
                spec = target_spec({}, mandatory=True)

                with assertRaises(BadTarget, "This task requires you specify a target"):
                    spec.normalise(Meta.empty(), val)

            @pytest.mark.parametrize("val", [None, "", sb.NotSpecified])
            def test_it_returns_not_specified_if_nothing_was_specified_and_isnt_mandatory(self, val):
                spec = target_spec({}, mandatory=False)
                assert spec.normalise(Meta.empty(), val) is sb.NotSpecified

    class TestWithAValue:
        @pytest.fixture()
        def superman(self):
            return mock.Mock(name="resolvedsuperman")

        @pytest.fixture()
        def batman(self):
            return mock.Mock(name="resolvedbatman")

        @pytest.fixture()
        def vegemite(self):
            return mock.Mock(name="resolvedvegemite")

        @pytest.fixture()
        def meta(self, superman, batman, vegemite, collector):
            reg = collector.configuration["target_register"]

            HeroTarget = mock.Mock(name="HeroTarget")
            herotarget = Target.FieldSpec().empty_normalise(type="hero")
            reg.register_type("hero", HeroTarget)

            VillianTarget = mock.Mock(name="VillianTarget")
            villiantarget = Target.FieldSpec().empty_normalise(type="villian")
            reg.register_type("villian", VillianTarget)

            supermancreator = mock.Mock(name="supermancreator", return_value=superman)
            reg.add_target("superman", herotarget, supermancreator)

            batmancreator = mock.Mock(name="batmancreator", return_value=batman)
            reg.add_target("batman", herotarget, batmancreator)

            vegemitecreator = mock.Mock(name="vegemitecreator", return_value=vegemite)
            reg.add_target("vegemite", villiantarget, vegemitecreator)

            return Meta({"collector": collector}, []).at("test")

        @pytest.mark.parametrize("mandatory", [True, False])
        def test_it_can_resolve_the_name(self, meta, mandatory, superman, vegemite):
            assert target_spec({}, mandatory=mandatory).normalise(meta, "superman") is superman
            assert target_spec({}, mandatory=mandatory).normalise(meta, "vegemite") is vegemite

        @pytest.mark.parametrize("mandatory", [True, False])
        def test_it_can_resolve_the_target_if_its_already_been_resolved_in_the_past(self, meta, mandatory, superman, vegemite):
            with assertRaises(TargetNotFound):
                target_spec({}, mandatory=mandatory).normalise(meta, superman)
            assert target_spec({}, mandatory=mandatory).normalise(meta, "superman") is superman
            assert target_spec({}, mandatory=mandatory).normalise(meta, superman) is superman

            assert target_spec({}, mandatory=mandatory).normalise(meta, "vegemite") is vegemite
            assert target_spec({}, mandatory=mandatory).normalise(meta, vegemite) is vegemite

        @pytest.mark.parametrize("mandatory", [True, False])
        def test_it_can_restrict_what_its_searching_for(self, meta, mandatory, superman, batman, vegemite):
            assert target_spec({}, mandatory=mandatory).normalise(meta, "superman") is superman
            with assertRaises(TargetNotFound):
                target_spec({"target_types": ["villian"]}, mandatory=mandatory).normalise(meta, "superman")
            with assertRaises(TargetNotFound):
                target_spec({"target_types": ["villian"]}, mandatory=mandatory).normalise(meta, superman)

            assert target_spec({"target_types": ["villian"]}, mandatory=mandatory).normalise(meta, "vegemite") is vegemite

            assert target_spec({"target_names": ["batman"]}, mandatory=mandatory).normalise(meta, "batman") is batman
            assert target_spec({"target_names": ["batman"]}, mandatory=mandatory).normalise(meta, batman) is batman


class TestReferenceSpec:
    class TestWithoutAValue:
        class TestMandatory:
            @pytest.mark.parametrize("val", [None, "", sb.NotSpecified])
            @pytest.mark.parametrize("special", [True, False])
            def test_it_complains_if_nothing_was_specified_and_is_mandatory(self, val, special):
                spec = reference_spec(mandatory=True, special=special)

                with assertRaises(BadOption, "This task requires you specify a reference"):
                    spec.normalise(Meta.empty(), val)

            @pytest.mark.parametrize("val", [None, "", sb.NotSpecified])
            def test_it_returns_not_specified_if_nothing_was_specified_and_isnt_mandatory(self, val):
                spec = reference_spec(mandatory=False, special=False)
                assert spec.normalise(Meta.empty(), val) is sb.NotSpecified

            @pytest.mark.parametrize("val", [None, "", sb.NotSpecified])
            def test_it_returns_a_reference_object_if_nothing_but_not_mandatory(self, val, collector):
                spec = reference_spec(mandatory=False, special=True)
                assert isinstance(spec.normalise(Meta({"collector": collector}, []).at("test"), val), FoundSerials)

    class TestWithAValue:
        @pytest.fixture()
        def meta(self, collector):
            def resolve(s):
                return DeviceFinder.from_url_str(s)

            collector.configuration["reference_resolver_register"].add("match", resolve)

            return Meta({"collector": collector}, []).at("test")

        @pytest.mark.parametrize("special,mandatory", [(False, False), (False, True), (True, False), (True, True)])
        def test_it_returns_as_is_if_not_a_string(self, meta, special, mandatory):
            val = HardCodedSerials([])
            assert reference_spec(mandatory=mandatory, special=special).normalise(meta, val) is val

        @pytest.mark.parametrize("mandatory", [False, True])
        def test_it_returns_as_is_if_a_string_and_special_is_False(self, meta, mandatory):
            val = "stuffandthings"
            assert reference_spec(mandatory=mandatory, special=False).normalise(meta, val) is val

        @pytest.mark.parametrize("mandatory", [False, True])
        def test_it_creates_a_reference_object_if_special_is_true_and_val_is_a_string(self, meta, mandatory):
            spec = reference_spec(mandatory=mandatory, special=True)

            result = spec.normalise(meta, "match:cap=hev")
            assert isinstance(result, DeviceFinder)
            assert result.fltr.cap == ["hev"]

            with assertRaises(ResolverNotFound):
                spec.normalise(meta, "nup:blah")
