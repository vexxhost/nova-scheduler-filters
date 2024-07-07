# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

from nova import objects, test
from nova.tests.unit.scheduler import fakes
from oslo_utils.fixture import uuidsentinel as uuids

from nova_scheduler_filters.failure_domain_filter import FailureDomainFilter


class TestFailureDomainFilter(test.NoDBTestCase):

    def setUp(self):
        super(TestFailureDomainFilter, self).setUp()
        self.filt_cls = FailureDomainFilter()

    def test_no_scheduler_hint(self):
        """
        Ensures that the filter passes if no scheduler hint is provided.
        """

        host = fakes.FakeHostState("host1", "node1", {})
        spec_obj = objects.RequestSpec(context=mock.sentinel.ctx, scheduler_hints=None)
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))

    def test_no_instance_group(self):
        """
        Ensures that the filter passes if the instance is not part of a
        server group.
        """

        host = fakes.FakeHostState("host1", "node1", {})
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            scheduler_hints=dict(different_failure_domain=["true"]),
            instance_group=None,
        )
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch("nova.objects.AggregateList.get_by_host")
    def test_host_not_in_failure_domain(self, mock_get_by_host):
        """
        Ensures that the filter fails if the host does not belong to any
        failure domain.
        """

        host = fakes.FakeHostState("host1", "node1", {"aggregates": []})
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            scheduler_hints=dict(different_failure_domain=["true"]),
            instance_group=objects.InstanceGroup(hosts=[uuids.host2]),
        )
        mock_get_by_host.return_value = []
        self.assertFalse(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch("nova.objects.AggregateList.get_by_host")
    def test_empty_server_group_with_no_failure_domain(self, mock_get_by_host):
        """
        Ensures that the filter fails if the server group is empty and the
        host does not belong to any failure domain.
        """

        host = fakes.FakeHostState("host1", "node1", {})
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            scheduler_hints=dict(different_failure_domain=["true"]),
            instance_group=objects.InstanceGroup(hosts=[]),
        )
        self.assertFalse(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch("nova.objects.AggregateList.get_by_host")
    def test_empty_server_group_with_failure_domain(self, mock_get_by_host):
        """
        Ensures that the filter passes if the server group is empty and the
        host belongs to a failure domain.
        """

        host = fakes.FakeHostState(
            "host1",
            "node1",
            {"aggregates": [objects.Aggregate(metadata={"failure_domain": "domain1"})]},
        )
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            scheduler_hints=dict(different_failure_domain=["true"]),
            instance_group=objects.InstanceGroup(hosts=[]),
        )
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch("nova.objects.AggregateList.get_by_host")
    def test_different_failure_domain(self, mock_get_by_host):
        """
        Ensures that the filter passes if the host belongs to a different
        failure domain compared to other hosts in the server group.
        """

        host = fakes.FakeHostState(
            "host1",
            "node1",
            {"aggregates": [objects.Aggregate(metadata={"failure_domain": "domain1"})]},
        )
        other_host_aggregates = [
            objects.Aggregate(hosts=["host2"], metadata={"failure_domain": "domain2"})
        ]
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            scheduler_hints=dict(different_failure_domain=["true"]),
            instance_group=objects.InstanceGroup(hosts=[uuids.host2]),
        )
        mock_get_by_host.return_value = other_host_aggregates
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch("nova.objects.AggregateList.get_by_host")
    def test_same_failure_domain(self, mock_get_by_host):
        """
        Ensures that the filter fails if the host belongs to the same failure
        domain as another host in the server group.
        """

        host = fakes.FakeHostState(
            "host1",
            "node1",
            {"aggregates": [objects.Aggregate(metadata={"failure_domain": "domain1"})]},
        )
        other_host_aggregates = [
            objects.Aggregate(hosts=["host2"], metadata={"failure_domain": "domain1"})
        ]
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            scheduler_hints=dict(different_failure_domain=["true"]),
            instance_group=objects.InstanceGroup(hosts=[uuids.host2]),
        )
        mock_get_by_host.return_value = other_host_aggregates
        self.assertFalse(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch("nova.objects.AggregateList.get_by_host")
    def test_other_host_not_in_failure_domain(self, mock_get_by_host):
        """
        Ensures that the filter passes if the other host in the server group
        does not belong to any failure domain.
        """

        host = fakes.FakeHostState(
            "host1",
            "node1",
            {"aggregates": [objects.Aggregate(metadata={"failure_domain": "domain1"})]},
        )
        other_host_aggregates = []
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            scheduler_hints=dict(different_failure_domain=["true"]),
            instance_group=objects.InstanceGroup(hosts=[uuids.host2]),
        )
        mock_get_by_host.return_value = other_host_aggregates
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))
