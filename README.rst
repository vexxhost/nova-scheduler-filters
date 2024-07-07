======================
Nova Scheduler Filters
======================

This project contains a set of filters for the Nova scheduler.  These filters
are intended to be used in conjunction with the default filters that ship with
Nova.

The goal of those filters are to provide additional filtering capabilities
that can be co-installed with any version of Nova until the features are
upstreamed.

--------------
Failure domain
--------------

The failure domain filter is a filter that can be used to spread instances
across different failure domains.  A failure domain is a set of compute nodes
that are expected to fail together.  For example, compute nodes in the same
rack or in the same power distribution unit (PDU) are expected to fail
together.

Historically, some users have used the availability zone feature to spread
instances across failure domains.  However, the availability zone feature is
not designed for this purpose and it has some limitations.  There is also
a need to spread instances across failure domains within the same availability
zone.

The failure domain is defined as a metadata on host aggregates.  The key of
the metadata is ``failure_domain``.  The value of the metadata is a string that
identifies the failure domain.  The failure domain filter will spread instances
across different failure domains.  It is up to the operator to define the
failure domains.
