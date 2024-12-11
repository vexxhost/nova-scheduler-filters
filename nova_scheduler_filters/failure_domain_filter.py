# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from nova import context as nova_context
from nova import objects
from nova.scheduler import filters
from oslo_log import log as logging
from oslo_utils import strutils

LOG = logging.getLogger(__name__)


class FailureDomainFilter(filters.BaseHostFilter):
    """
    Filter to ensure instances in a server group are placed in different
    failure domains.
    """

    RUN_ON_REBUILD = False

    def host_passes(self, host_state, spec_obj):
        # Include the host if the scheduler hint is set to false (or unset)
        if (
            strutils.bool_from_string(
                spec_obj.get_scheduler_hint("different_failure_domain")
            )
            is False
        ):
            return True

        # Include the host if the instance is not in a server group
        instance_group = spec_obj.instance_group
        if not instance_group:
            return True

        # Get the failure domain of the host
        failure_domain = self._get_failure_domain(host_state)

        # Skip the host if it does not belong to any failure domain
        if not failure_domain:
            LOG.debug(
                "Host %(host)s does not belong to any failure domain.",
                {
                    "host": host_state.host,
                },
            )
            return False

        # Include the host if the server group is empty
        if not instance_group.hosts:
            return True

        # Get the admin context
        context = nova_context.get_admin_context()

        # Check failure domains of the hosts already in the server group
        for other_host in instance_group.hosts:
            # Get the host aggregates of the other host
            other_aggregates = objects.AggregateList.get_by_host(context, other_host)

            # Get failure domain of the other host
            other_failure_domain = None
            for other_aggregate in other_aggregates:
                if "failure_domain" in other_aggregate.metadata:
                    other_failure_domain = other_aggregate.metadata["failure_domain"]
                    break

            # Include the host if the other host does not belong to any failure domain
            # but log a warning
            if not other_failure_domain:
                LOG.warning(
                    "Host %(host)s does not belong to any failure domain.",
                    {
                        "host": other_host,
                    },
                )
                continue

            # Skip the host if the other host matches the current host
            if failure_domain == other_failure_domain:
                LOG.debug(
                    "Host %(host)s is in the same failure domain %(failure_domain)s "
                    "as another host in the server group",
                    {"host": host_state.host, "failure_domain": failure_domain},
                )
                return False

        # Include the host if no hosts in the same failure domain
        return True

    def _get_failure_domain(self, host_state):
        """
        Retrieve the failure domain from the host's aggregates, return None if
        the host does not belong to any failure domain.
        """

        for aggregate in host_state.aggregates:
            if "failure_domain" in aggregate.metadata:
                return aggregate.metadata["failure_domain"]

        return None
