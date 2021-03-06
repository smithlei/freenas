import asyncio
import libzfs
import os
import sysctl

from datetime import datetime

from middlewared.schema import accepts, Int
from middlewared.service import filterable, item_method, private, CRUDService


class PoolService(CRUDService):

    @filterable
    async def query(self, filters=None, options=None):
        filters = filters or []
        options = options or {}
        options['extend'] = 'pool.pool_extend'
        options['prefix'] = 'vol_'
        return await self.middleware.call('datastore.query', 'storage.volume', filters, options)

    @private
    async def pool_extend(self, pool):
        pool.pop('fstype', None)

        """
        If pool is encrypted we need to check if the pool is imported
        or if all geli providers exist.
        """
        try:
            zpool = libzfs.ZFS().get(pool['name'])
        except libzfs.ZFSException:
            zpool = None

        if zpool:
            pool['status'] = zpool.status
            pool['scan'] = zpool.scrub.__getstate__()
        else:
            pool.update({
                'status': 'OFFLINE',
                'scan': None,
            })

        if pool['encrypt'] > 0:
            if zpool:
                pool['is_decrypted'] = True
            else:
                decrypted = True
                for ed in await self.middleware.call('datastore.query', 'storage.encrypteddisk', [('encrypted_volume', '=', pool['id'])]):
                    if not os.path.exists(f'/dev/{ed["encrypted_provider"]}.eli'):
                        decrypted = False
                        break
                pool['is_decrypted'] = decrypted
        else:
            pool['is_decrypted'] = True
        return pool

    @item_method
    @accepts(Int('id'))
    async def get_disks(self, oid):
        """
        Get all disks from a given pool `id`.
        """
        pool = await self.query([('id', '=', oid)], {'get': True})
        if not pool['is_decrypted']:
            yield
        async for i in await self.middleware.call('zfs.pool.get_disks', pool['name']):
            yield i

    @private
    def configure_resilver_priority(self):
        """
        Configure resilver priority based on user selected off-peak hours.
        """
        resilver = self.middleware.call_sync('datastore.config', 'storage.resilver')

        if not resilver['enabled'] or not resilver['weekday']:
            return

        higher_prio = False
        weekdays = map(lambda x: int(x), resilver['weekday'].split(','))
        now = datetime.now()
        now_t = now.time()
        # end overlaps the day
        if resilver['begin'] > resilver['end']:
            if now.isoweekday() in weekdays and now_t >= resilver['begin']:
                higher_prio = True
            else:
                lastweekday = now.isoweekday() - 1
                if lastweekday == 0:
                    lastweekday = 7
                if lastweekday in weekdays and now_t < resilver['end']:
                    higher_prio = True
        # end does not overlap the day
        else:
            if now.isoweekday() in weekdays and now_t >= resilver['begin'] and now_t < resilver['end']:
                higher_prio = True

        if higher_prio:
            resilver_delay = 0
            resilver_min_time_ms = 9000
            scan_idle = 0
        else:
            resilver_delay = 2
            resilver_min_time_ms = 3000
            scan_idle = 50

        sysctl.filter('vfs.zfs.resilver_delay')[0].value = resilver_delay
        sysctl.filter('vfs.zfs.resilver_min_time_ms')[0].value = resilver_min_time_ms
        sysctl.filter('vfs.zfs.scan_idle')[0].value = scan_idle


def setup(middleware):
    asyncio.ensure_future(middleware.call('pool.configure_resilver_priority'))
