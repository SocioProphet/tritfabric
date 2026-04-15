from atlas.scheduler.drf import DRFBroker


def test_drf_prefers_lower_dominant_share():
    b = DRFBroker(tenant_weights={"A": 1.0, "B": 1.0})
    b.set_cluster_total({"CPU": 10, "GPU": 0, "MEM": 10})

    b.submit("A", "A1", {"resources": {"CPU": 5}})
    b.submit("A", "A2", {"resources": {"CPU": 5}})
    b.submit("B", "B1", {"resources": {"CPU": 5}})

    # First pick: A1 (FIFO tie)
    t, jid, req = b.pick({"CPU": 10, "GPU": 0, "MEM": 10})
    assert (t, jid) == ("A", "A1")

    # Next pick should be B1 (A would dominate if it took another 5 CPU)
    t, jid, req = b.pick({"CPU": 10, "GPU": 0, "MEM": 10})
    assert (t, jid) == ("B", "B1")

def test_drf_release_reduces_allocation():
    b = DRFBroker(tenant_weights={"A": 1.0})
    b.set_cluster_total({"CPU": 10, "GPU": 0, "MEM": 10})
    b.submit("A", "A1", {"resources": {"CPU": 5}})
    t, jid, req = b.pick({"CPU": 10, "GPU": 0, "MEM": 10})
    assert (t, jid) == ("A", "A1")
    assert b.alloc["A"]["CPU"] == 5.0
    b.release("A", {"resources": {"CPU": 5}})
    assert b.alloc["A"]["CPU"] == 0.0
