from dsportal.base import healthcheckfn
from dsportal.util import get_ups_data,bar_percentage
import os
import multiprocessing
import requests

class RamUsage(HealthCheck):
    label = "RAM Usage"
    description = "Checks RAM usage is less than 90%. Does not count cache and buffers."

    @staticmethod
    def check():
        # http://www.linuxatemyram.com/
        with open('/proc/meminfo') as f:
            lines = f.readlines()

        # in kB
        info = {}

        for line in lines:
            m = re.search('(\w+):\s*(\d+)', line)
            if m:
                info[m.group(1)] = int(m.group(2))

        used = info['MemTotal'] - info['MemFree'] - info['Buffers'] - info['Cached']

        total = info['MemTotal'] * 1024

        # used by applications, not cache/buffers
        value = used * 1024

        return {
                "value": value,
                "bar_min": "0MB",
                "bar_max": human_bytes(total), # TODO standardise way of representing magnitude
                "bar_percentage": bar_percentage(value,total),
                "healthy": value < (0.9*total)/100,
                }

class CpuUsage(HealthCheck):
    label = "CPU Utilisation"
    description = "Checks CPU load is nominal."

    @staticmethod
    def check(_max=200):
        #"return normalised % load (avg num of processes waiting per processor)"
        load = os.getloadavg()[0]
        load = load / multiprocessing.cpu_count()
        value = int(load*100)
        return {
                "value": value,
                "bar_min":"0%",
                "bar_max":"100%",
                "bar_percentage": bar_percentage(value,100),
                "healthy": value < _max,
                }


# TODO mountpoint needs to be in label FIXME
class DiskUsage(HealthCheck):
    label = "Disk Usage"
    description = "Inspects used and available blocks on given mount points."
    @staticmethod
    def check(mountpoint='/'):
        s = statvfs(mountpoint)
        free = s.f_bsize * s.f_bavail
        total = s.f_bsize * s.f_blocks
        usage = total - free

        return {
                "value": value,
                "bar_min": "0MB",
                "bar_max": human_bytes(total), # TODO standardise way of representing magnitude
                "bar_percentage": bar_percentage(usage,total),
                "healthy": usage < (0.8*total)/100,
                }


class UpsVoltage(HealthCheck):
    label = "Mains Voltage"
    description = "Checks mains voltage falls within UK statutory limits of 230V +10% -6%"
    @staticmethod
    def check(_min=216,_max=253):
        info = util.get_ups_data()
        return {
            "bar_min":'%sV' % _min,
            "bar_max":'%sV' % _max,
            'bar_percentage': bar_percentage(info['LINEV'],_max,_min),
            'value': info['LINEV'],
            "healthy": (info['LINEV'] < _max) and (info['LINEV'] > _max),
        }

class UpsLoad(HealthCheck):
    label = "UPS Load"
    description = "Checks UPS is not overloaded"
    @staticmethod
    def check():
        info = util.get_ups_data()
        return {
            "bar_min":"0%",
            "bar_max":"100%",
            'bar_percentage': info['LOADPCT'],
            'value': '%s%%' % info['LOADPCT'],
            "healthy": info['LOADPCT'] < 90,
        }

class UpsBattery(HealthCheck):
    label = "UPS battery"
    description = "Checks estimated time remaining and percentage"
    @staticmethod
    def check():
        info = util.get_ups_data()
        return {
            "bar_min":"0%",
            "bar_max":"100%",
            'bar_percentage': info['BCHARGE'],
            'value': info['TIMELEFT'], # ???
            "healthy": info['TIMELEFT'] < 300,
        }


class Uptime(HealthCheck):
    label = "Uptime"
    description = "Specify uptime in days"

    @staticmethod
    def check():
        with open('/proc/uptime', 'r') as f:
            line = f.readline()

        seconds = line.partition(' ')[0]
        seconds = float(seconds)

        days = int(round(seconds/86400))

        return {
            "healthy": True,
            "value": '%s days' % days,
            }


class CpuTemperature(HealthCheck):
    label = "CPU Temperature"
    description = "Checks CPU Temperature is nominal"

class GpuTemperature(HealthCheck):
    label = "GPU Temperature"
    description = "Checks GPU Temperature is nominal"

    @staticmethod
    def check():
        process = Popen(['nvidia-smi', '-q', '-d', 'TEMPERATURE'],
                        stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out, _ = process.communicate()

        state = dict()
        for line in out.splitlines():
            try:
                key, val = line.split(":")
            except ValueError:
                continue
            key, val = key.strip(), val.strip()
            state[key] = val

        int(state['GPU Current Temp'][:-2])

        try:
            int(state['GPU Shutdown Temp'][:-2])
            int(state['GPU Slowdown Temp'][:-2])
        except ValueError:
            # not specified, so dot change the classaults
            pass



class BtrfsPool(HealthCheck):
    label = "BTRFS Pool"
    description = "Checks BTRFS health"

class HttpStatus(HealthCheck):
    label = "HTTP check"
    description = "Checks service returns 200 OK"
    @staticmethod
    def check(url,timeout=10):
        r = requests.get(url,timeout=timeout)
        r.raise_for_status()

        return {
                "healthy": True,
                }

class BrokenLinks(HealthCheck):
    label = "Hyperlinks"
    description = "Crawls website for broken links"
    interval = 5*60*60
    @staticmethod
    def check(url,ignore):
        # https://wummel.github.io/linkchecker/ but use git to install latest revision
        # example linkchecker --check-html --check-css --ignore-url 'xmlrpc.php' --user-agent 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.  110 Safari/537.36' https://cydarmedical.com
        pass

# run time -- 5 mins or so for small website
# run every 5 hours

class CertificateExpiry(HealthCheck):
    "Checks certificate isn't near expiry"
    # https://stackoverflow.com/questions/7689941/how-can-i-retrieve-the-tls-ssl-peer-certificate-of-a-remote-host-using-python

class s3_backup_checker(HealthCheck):
    label = "S3 daily backup"
    description = "Checks to see that a backup was made in the last 25 hours"
    @staticmethod
    def check(bucket,hours=25):
        # list keys in bucket and check the latest upload was < 25 hours ago.
        pass

class PapouchTh2eTemperature(HealthCheck)
    label = "Server room Temperature"
    description = "Checks the temperature reported by a Papouch TH2E"

    @staticmethod
    def check(
        url,
        min_temp=10,
        max_temp=35,
        min_hum=20,
        max_hum=80):
        pass



class SsllabsReport(HealthCheck):
    title = "SSL implementation"
    description = "Checks SSL implementation using ssllabs.org"
    @staticmethod
    def check(host,min_grade='A+'):
        grades = ['A+','A','A-','B','C','D','E','F','T','M']
        grades = dict(zip(grades,range(len(grades)))) # grade -> score

        for x in range(100):
            response = requests.get('https://api.ssllabs.com/api/v2/analyze',params={
                "host": host,
                },timeout=5)
            response.raise_for_status()
            report = response.json()
            sleep(2)

            if report['status'] == 'READY':
                break

            if report['status'] == 'ERROR':
                raise Exception(report['statusMessage'])
        else:
            raise TimeoutError('SSL labs test took too long')

        grade = report['endpoints'][0]['grade']

        if grades[grade] >= grades[min_grade]:
            raise Exception('Grade %s not acheived, got %s.' % (min_grade,grade))

        return {
            'healthy': True,
                }

    class PortScan(open_ports=[22,80,443],limit=1024):
        '''asserts that the given ports are listening and no others are.'''
        pass
