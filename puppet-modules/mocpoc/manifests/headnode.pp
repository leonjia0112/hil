# Sets up an ubuntu 12.04 machine as a headnode for mocpoc-head.
#
# Parameters:
# [slave_rootpw]: the encrypted root password to use on slave nodes (mandatory).
class mocpoc::headnode (
	$slave_rootpw,
) {
	$tftpdir = '/var/lib/tftpboot'
	$syslinux_files = [
		"${tftpdir}/pxelinux.0",
		"${tftpdir}/menu.c32",
		"${tftpdir}/memdisk",
		"${tftpdir}/mboot.c32",
		"${tftpdir}/chain.c32",
	]
	# We need a few packages for our head nodes:
	package { [
		'isc-dhcp-server',
		'tftpd-hpa',
		'syslinux-common',
		'fcgiwrap',
		'nginx',
		] :
		ensure => 'installed',
	}
	# We only want the dhcp server listening on eth0. This file handles that:
	file { '/etc/default/isc-dhcp-server':
		content => 'INTERFACES="eth0"\n',
		require => Package['isc-dhcp-server'],
	}
	# Create subdirectories in the tftp root.
	file { [
		"${tftpdir}/pxelinux.cfg",
		"${tftpdir}/centos"
		] :
		ensure => 'directory',
		require => Package['tftpd-hpa'],
	}
	file { "${tftpdir}/centos/ks.cfg":
		require => File["${tftpdir}/centos"],
		content => template('mocpoc/ks.cfg.erb'),
	}
	file { "${tftpdir}/centos/vmlinuz":
		require => File["${tftpdir}/centos"],
		source => 'puppet:///modules/mocpoc/headnode/vmlinuz',
	}
	file { "${tftpdir}/centos/initrd.img":
		require => File["${tftpdir}/centos"],
		source => 'puppet:///modules/mocpoc/headnode/initrd.img',
	}
	Package['tftpd-hpa'] -> File[$syslinux_files]
	Package['syslinux-common'] -> File[$syslinux_files]

	# Copy the bootloader into the tftp directory:
	file { "${tftpdir}/pxelinux.0":
		source => '/usr/lib/syslinux/pxelinux.0',
	}
	file { "${tftpdir}/menu.c32":
		source => '/usr/lib/syslinux/menu.c32',
		require => Package['syslinux-common'],
	}
	file { "${tftpdir}/memdisk":
		source => '/usr/lib/syslinux/memdisk',
	}
	file { "${tftpdir}/mboot.c32":
		source => '/usr/lib/syslinux/mboot.c32',
	}
	file { "${tftpdir}/chain.c32":
		source => '/usr/lib/syslinux/chain.c32',
	}
	# make sure dhcpd is configured correctly:
	file { '/etc/dhcp/dhcpd.conf':
		source => 'puppet:///modules/mocpoc/headnode/dhcpd.conf',
		require => Package['isc-dhcp-server'],
	}
	# make sure the network setup is correct:
	file { '/etc/network/interfaces':
		source => 'puppet:///modules/mocpoc/headnode/interfaces',
		notify => Service['networking'],
	}
	file { '/etc/iptables':
		source => 'puppet:///modules/mocpoc/headnode/iptables',
		notify => Service['networking'],
	}
	# boot nodes to the disk by default:
	file { "${tftpdir}/pxelinux.cfg/default":
		content => '
		default disk
		label disk
			LOCALBOOT 0
		',
		require => File["${tftpdir}/pxelinux.cfg"],
	}
	# make the tftp directory available via http as well - this is needed for kickstart to work:
	file { '/etc/nginx/sites-enabled/tftp':
		source => 'puppet:///modules/mocpoc/headnode/nginx-tftp',
		require => Package['nginx'],
	}
	# Mount the virtio filesystem on boot (This doesn't seem to work from fstab):
	file { '/etc/rc.local':
		content => '
		mount -t 9p -o ro,trans=virtio /etc/moc /etc/moc
		'
	}

	service { [
		'networking',
		'nginx',
		'isc-dhcp-server',
		'tftpd-hpa',
		] :
		ensure => running,
	}
	# TODO:
	# - most of ${tftpdir}/centos.
	#
	#   Conceptually, we want something like this, to grab the boot images for
	#   centos:
	#
	#   $centos_mirror = 'http://mirror.mit.edu/centos/6.4/os/x86_64/'
	#   file { "${tftpdir}/centos/vmlinuz":
	#   	source => "${centos_mirror}/isolinux/vmlinuz",
	#   }
	#   file { "${tftpdir}/centos/initrd.img":
	#   	source => "${centos_mirror}/isolinux/initrd.img",
	#   }
	#
	#   Unfortunately, this won't work since puppet can't use an http url as a
	#   source. It's also at least questionable from a security standpoint.
	# - puppet master
	# - python-mocutils
}