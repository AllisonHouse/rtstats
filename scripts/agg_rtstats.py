"""Aggregate the hourly rtstats"""
import rtstats_util as util
import datetime
import pytz


def daily():
    pgconn = util.get_dbconn(rw=True)
    cursor = pgconn.cursor()
    # we run for the day for the previous hour
    utcnow = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    utcnow = utcnow.replace(tzinfo=pytz.utc)
    sts = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)
    ets = sts + datetime.timedelta(hours=24)
    cursor.execute("""
        DELETE from ldm_rtstats_daily WHERE valid = %s
        """, (sts.date(),))
    cursor.execute("""
    WITH hourly as (
        select feedtype_path_id, date_trunc('hour', queue_arrival) as v,
        count(*), max(nprods) as max_nprods, max(nbytes) as max_nbytes,
        min(avg_latency) as minl, avg(avg_latency) as avgl,
        max(avg_latency) as maxl from ldm_rtstats
        WHERE queue_arrival >= %s
        and queue_arrival < %s
        GROUP by feedtype_path_id, v),
    agg as (
        SELECT feedtype_path_id, %s as v, sum(count), sum(max_nprods),
        sum(max_nbytes), min(minl), avg(avgl), max(maxl) from hourly
        GROUP by feedtype_path_id)
    INSERT into ldm_rtstats_daily SELECT * from agg
    """, (sts.date(), sts, ets))
    cursor.close()
    pgconn.commit()
    pgconn.close()


def hourly():
    pgconn = util.get_dbconn(rw=True)
    cursor = pgconn.cursor()
    # figure out what our most recent stats are for
    cursor.execute("""SELECT max(valid) from ldm_rtstats_hourly""")
    maxval = cursor.fetchone()[0]
    cursor.execute("""
    WITH agg as (
        select feedtype_path_id, date_trunc('hour', queue_arrival) as v,
        count(*), max(nprods), max(nbytes),
        min(avg_latency), avg(avg_latency), max(max_latency) from ldm_rtstats
        WHERE queue_arrival >= %s + '1 hour'::interval
        and queue_arrival < date_trunc('hour', now())
        GROUP by feedtype_path_id, v)
    INSERT into ldm_rtstats_hourly SELECT * from agg
    """, (maxval or datetime.datetime(1971, 1, 1), ))
    cursor.close()
    pgconn.commit()
    pgconn.close()

if __name__ == '__main__':
    daily()
    hourly()
