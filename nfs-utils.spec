Summary:	The utilities for Linux NFS server
Name:		nfs-utils
Epoch:		1
Version:	1.2.8
Release:	7
Group:		Networking/Other
License:	GPLv2
Url:		http://sourceforge.net/projects/nfs/
Source0:	http://prdownloads.sourceforge.net/nfs/%{name}-%{version}.tar.bz2
Source6:	nfsv4.schema
Source7:	gssapi_mech.conf
Source8:	idmapd.conf
Source9:	id_resolver.conf
Source10:	nfs.sysconfig

Source11:	nfs-lock.service
Source12:	nfs-secure.service
Source13:	nfs-secure-server.service
Source14:	nfs-server.service
Source15:	nfs-blkmap.service
Source16:	nfs-rquotad.service
Source17:	nfs-mountd.service
Source18:	nfs-idmap.service
Source19:	nfs.target
%define nfs_services %{SOURCE11} %{SOURCE12} %{SOURCE13} %{SOURCE14} %{SOURCE15} %{SOURCE16} %{SOURCE17} %{SOURCE18} %{SOURCE19}

Source20:	var-lib-nfs-rpc_pipefs.mount
Source21:	proc-fs-nfsd.mount
%define nfs_automounts %{SOURCE20} %{SOURCE21}

Source50:	nfs-lock.preconfig
Source51:	nfs-server.preconfig
Source52:	nfs-server.postconfig
%define nfs_configs %{SOURCE50} %{SOURCE51} %{SOURCE52}

Source60:	nfs4-modalias.conf

Patch100:	nfs-utils-1.2.1-statdpath-man.patch
Patch101:	nfs-utils-1.2.1-exp-subtree-warn-off.patch
Patch102:	nfs-utils-1.2.3-sm-notify-res_init.patch
Patch103:	nfs-utils-1.2.5-idmap-errmsg.patch

BuildRequires:  keyutils-devel
BuildRequires:	krb5-devel >= 1.3
BuildRequires:	libcap-devel
BuildRequires:	wrap-devel
BuildRequires:	pkgconfig(blkid)
BuildRequires:  pkgconfig(devmapper)
BuildRequires:	pkgconfig(libevent)
BuildRequires:	pkgconfig(libnfsidmap) >= 0.16
BuildRequires:	pkgconfig(librpcsecgss)
BuildRequires:	pkgconfig(libtirpc)
Requires(pre,post,preun,postun):	rpm-helper
Requires:	rpcbind
Requires:	tcp_wrappers
%rename		nfs-utils-clients 

%description
This package provides various programs needed for NFS support on server.

%prep
%setup -q
%apply_patches
find . -name *.o -delete


%build
%serverbuild
%configure2_5x \
	--with-statdpath=%{_localstatedir}/lib/nfs/statd \
	--with-statduser=rpcuser \
	--enable-nfsv4 \
	--enable-ipv6 \
	--enable-gss \
	--enable-tirpc \
	--with-krb5=%{_prefix} \
	--enable-mountconfig

make all CFLAGS="%{optflags} -DDEBUG"

%install
install -d %{buildroot}{/sbin,/usr/sbin}
install -d %{buildroot}%{_mandir}/{man5,man8}

%make \
	DESTDIR=%{buildroot} \
	MANDIR=%{buildroot}%{_mandir} \
	SBINDIR=%{buildroot}%{_prefix}/sbin \
	install

install -m 755 tools/rpcdebug/rpcdebug %{buildroot}/sbin/
ln -snf rpcdebug %{buildroot}/sbin/nfsdebug
ln -snf rpcdebug %{buildroot}/sbin/nfsddebug

install -d %{buildroot}%{_sysconfdir}
install -m 644 utils/mount/nfsmount.conf %{buildroot}%{_sysconfdir}

install -d %{buildroot}%{_sysconfdir}/request-key.d
install -m 644 %{SOURCE9} %{buildroot}%{_sysconfdir}/request-key.d

install -d %{buildroot}%{_sysconfdir}/sysconfig
install -m 644 %{SOURCE10} %{buildroot}%{_sysconfdir}/sysconfig/nfs

install -d %{buildroot}%{_sysconfdir}/modprobe.d
install -m 644 %{SOURCE60} %{buildroot}%{_sysconfdir}/modprobe.d/nfs.conf

install -d %{buildroot}%{_unitdir}
install -d %{buildroot}/usr/lib/%{name}/scripts
for service in %{nfs_services} ; do
	install -m 644 $service %{buildroot}%{_unitdir}
done
for service in %{nfs_automounts} ; do
	install -m 644 $service %{buildroot}%{_unitdir}
done
for config in %{nfs_configs} ; do
	install -m 755 $config %{buildroot}/usr/lib/%{name}/scripts
done

install -d %{buildroot}%{_localstatedir}/lib/nfs/rpc_pipefs

touch %{buildroot}%{_localstatedir}/lib/nfs/rmtab
mv %{buildroot}%{_sbindir}/rpc.statd %{buildroot}/sbin/

install -d %{buildroot}%{_localstatedir}/lib/nfs/statd/sm
install -d %{buildroot}%{_localstatedir}/lib/nfs/statd/sm.bak
install -d %{buildroot}%{_localstatedir}/lib/nfs/v4recovery
install -d %{buildroot}%{_sysconfdir}/exports.d

install -m 644 %{SOURCE7} %{buildroot}%{_sysconfdir}/gssapi_mech.conf
install -m 644 %{SOURCE8} %{buildroot}%{_sysconfdir}/idmapd.conf
sed -i -e "s|/usr/lib|%{_libdir}|g" %{buildroot}%{_sysconfdir}/gssapi_mech.conf

# nuke dupes
rm -f %{buildroot}%{_sbindir}/rpcdebug

cat >%{buildroot}%{_sysconfdir}/exports <<EOF
# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
EOF

# manage documentation manually
install -d -m 755 %{buildroot}%{_docdir}/%{name}
install -m 644 README COPYING NEWS %{SOURCE6} \
    %{buildroot}%{_docdir}/%{name}

# fix perms
chmod 0755 %{buildroot}/sbin/mount.nfs

%pre
%_pre_useradd rpcuser %{_localstatedir}/lib/nfs /bin/false

%postun
%_postun_userdel rpcuser

%files
%{_docdir}/%{name}
%dir %{_localstatedir}/lib/nfs
%dir %{_localstatedir}/lib/nfs/v4recovery
%dir %{_localstatedir}/lib/nfs/rpc_pipefs
%dir %{_sysconfdir}/exports.d
%dir %attr(700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd
%dir %attr(700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd/sm
%dir %attr(700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd/sm.bak
%config(noreplace) %attr(644,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/state
%config(noreplace) %{_localstatedir}/lib/nfs/xtab
%config(noreplace) %{_localstatedir}/lib/nfs/etab
%config(noreplace) %{_localstatedir}/lib/nfs/rmtab
%config(noreplace) %{_sysconfdir}/request-key.d/id_resolver.conf
%config(noreplace) %{_sysconfdir}/exports
%config(noreplace) %{_sysconfdir}/sysconfig/nfs
%config(noreplace) %{_sysconfdir}/nfsmount.conf
%config(noreplace) %{_sysconfdir}/idmapd.conf
%config(noreplace) %{_sysconfdir}/gssapi_mech.conf
%{_sysconfdir}/modprobe.d/nfs.conf
%{_unitdir}/*
/usr/lib/%{name}/scripts/*
/sbin/nfsddebug
/sbin/rpc.statd
/sbin/mount.nfs
/sbin/mount.nfs4
/sbin/umount.nfs
/sbin/umount.nfs4
/sbin/rpcdebug
/sbin/nfsdebug
/sbin/osd_login
%{_sbindir}/exportfs
%{_sbindir}/rpc.mountd
%{_sbindir}/rpc.nfsd
%{_sbindir}/rpc.svcgssd
%{_sbindir}/sm-notify
%{_sbindir}/start-statd
%{_sbindir}/showmount
%{_sbindir}/mountstats
%{_sbindir}/nfsdcltrack
%{_sbindir}/nfsiostat
%{_sbindir}/nfsidmap
%{_sbindir}/blkmapd
%{_sbindir}/nfsstat
%{_sbindir}/rpc.idmapd
%{_sbindir}/rpc.gssd
%{_sbindir}/gss_clnt_send_err
%{_sbindir}/gss_destroy_creds
%{_mandir}/man5/exports.5*
%{_mandir}/man5/nfs.5*
%{_mandir}/man5/nfsmount.conf.5*
%{_mandir}/man7/nfsd.7*
%{_mandir}/man8/exportfs.8*
%{_mandir}/man8/mountd.8*
%{_mandir}/man8/nfsd.8*
%{_mandir}/man8/rpc.mountd.8*
%{_mandir}/man8/rpc.nfsd.8*
%{_mandir}/man8/rpc.svcgssd.8*
%{_mandir}/man8/svcgssd.8*
%{_mandir}/man8/mount.nfs.8*
%{_mandir}/man8/rpc.sm-notify.8*
%{_mandir}/man8/sm-notify.8*
%{_mandir}/man8/umount.nfs.8*
%{_mandir}/man8/rpc.statd.8*
%{_mandir}/man8/statd.8*
%{_mandir}/man8/showmount.8*
%{_mandir}/man8/nfsstat.8*
%{_mandir}/man8/rpcdebug.8*
%{_mandir}/man8/mountstats.8*
%{_mandir}/man8/nfsdcltrack.8*
%{_mandir}/man8/nfsiostat.8*
%{_mandir}/man8/nfsidmap.8*
%{_mandir}/man8/blkmapd.8*
%{_mandir}/man8/rpc.gssd.8*
%{_mandir}/man8/rpc.idmapd.8*
%{_mandir}/man8/gssd.8*
%{_mandir}/man8/idmapd.8*

