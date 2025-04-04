%define major 1
%define oldlibname %mklibname nfsidmap 1
%define libname %mklibname nfsidmap
%define devname %mklibname nfsidmap -d
%define _disable_ld_no_undefined 1

%global optflags %{optflags} -Wl,-z,notext

Summary:	The utilities for Linux NFS server
Name:		nfs-utils
Epoch:		1
Version:	2.8.3
Release:	1
Group:		Networking/Other
License:	GPLv2
Url:		https://linux-nfs.org/
# git clone git://git.linux-nfs.org/projects/steved/nfs-utils.git
# cd nfs-utils
# git archive -o nfs-utils-%{version}.tar --prefix nfs-utils-%{version}/ nfs-utils-$(echo %{version} |sed -e 's,\.,-,g')
# xz -9ef *.tar
Source0:	https://mirrors.edge.kernel.org/pub/linux/utils/nfs-utils/%{version}/%{name}-%{version}.tar.xz
Source6:	nfsv4.schema
Source7:	gssapi_mech.conf
Source8:	idmapd.conf
Source9:	id_resolver.conf
Source10:	nfs.sysconfig

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
Patch102:	nfs-utils-2.3.4-no-werror.patch
#Patch103:	nfs-utils-2.6.4-compile.patch

BuildRequires:  keyutils-devel
BuildRequires:  pkgconfig(com_err)
BuildRequires:	krb5-devel >= 1.3
BuildRequires:	pkgconfig(libcap)
BuildRequires:	wrap-devel
BuildRequires:	pkgconfig(blkid)
BuildRequires:  pkgconfig(devmapper)
BuildRequires:	pkgconfig(libevent)
BuildRequires:	pkgconfig(librpcsecgss)
BuildRequires:	pkgconfig(libtirpc)
BuildRequires:	pkgconfig(mount)
BuildRequires:	pkgconfig(sqlite3)
BuildRequires:	pkgconfig(libxml-2.0)
BuildRequires:	pkgconfig(libnl-3.0) >= 3.1
BuildRequires:	pkgconfig(readline)
BuildRequires:	systemd-macros
BuildRequires:	rpm-helper
Requires(pre,post,preun,postun):	rpm-helper
Requires:	rpcbind
Requires:	kmod
%rename		nfs-utils-clients 

%description
This package provides various programs needed for NFS support on server.

%package -n %{libname}
Summary:	Library to help mapping IDs, mainly for NFSv4
License:	BSD-like
Group:		System/Libraries
%rename %{oldlibname}

%description -n %{libname}
libnfsidmap is a library holding mulitiple methods of mapping
names to id's and visa versa, mainly for NFSv4.

When NFSv4 is using AUTH_GSS (which currently only supports
Kerberos v5), the NFSv4 server mapping functions MUST use
secure communications.

%package -n     %{devname}
Summary:	Development library and header files for the nfsidmap library
Group:		Development/C
License:	BSD-like
Requires:	%{libname} = %{EVRD}
Provides:	libnfsidmap-devel = %{EVRD}
Provides:	nfsidmap-devel  = %{EVRD}
Obsoletes:	%{_lib}nfsidmap0-devel < 0.25-3

%description -n %{devname}
This package contains the development libnfsidmap library and its
header files.

%prep
%autosetup -p1
find . -name *.o -delete
./autogen.sh --no-configure

%build
%serverbuild_hardened
%configure \
	--with-statdpath=%{_localstatedir}/lib/nfs/statd \
	--with-statduser=rpcuser \
	--with-systemd=%{_unitdir} \
	--enable-libmount-mount \
	--without-tcp-wrappers \
	--enable-nfsv4 \
	--enable-ipv6 \
	--enable-gss \
	--enable-tirpc \
	--with-krb5=%{_prefix} \
	--enable-mountconfig

make all CFLAGS="%{optflags} -DDEBUG -fPIC"

%install
install -d %{buildroot}%{_mandir}/{man5,man8}

%make \
	DESTDIR=%{buildroot} \
	sbindir=%{_bindir} \
	MANDIR=%{buildroot}%{_mandir} \
	install

install -m 755 tools/rpcdebug/rpcdebug %{buildroot}%{_bindir}
ln -s rpcdebug %{buildroot}%{_bindir}/nfsdebug
ln -s rpcdebug %{buildroot}%{_bindir}/nfsddebug

install -d %{buildroot}%{_sysconfdir}
install -m 644 utils/mount/nfsmount.conf %{buildroot}%{_sysconfdir}

install -d %{buildroot}%{_sysconfdir}/request-key.d
install -m 644 %{SOURCE9} %{buildroot}%{_sysconfdir}/request-key.d

install -d %{buildroot}%{_sysconfdir}/sysconfig
install -m 644 %{SOURCE10} %{buildroot}%{_sysconfdir}/sysconfig/nfs

install -d %{buildroot}%{_sysconfdir}/modprobe.d
install -m 644 %{SOURCE60} %{buildroot}%{_sysconfdir}/modprobe.d/nfs.conf

install -d %{buildroot}%{_prefix}/lib/%{name}/scripts
for config in %{nfs_configs} ; do
	install -m 755 $config %{buildroot}%{_prefix}/lib/%{name}/scripts
done

install -d %{buildroot}%{_localstatedir}/lib/nfs/rpc_pipefs

touch %{buildroot}%{_localstatedir}/lib/nfs/rmtab

install -d %{buildroot}%{_localstatedir}/lib/nfs/statd/sm
install -d %{buildroot}%{_localstatedir}/lib/nfs/statd/sm.bak
install -d %{buildroot}%{_localstatedir}/lib/nfs/v4recovery
install -d %{buildroot}%{_sysconfdir}/exports.d

install -m 644 %{SOURCE7} %{buildroot}%{_sysconfdir}/gssapi_mech.conf
install -m 644 %{SOURCE8} %{buildroot}%{_sysconfdir}/idmapd.conf
sed -i -e "s|/usr/lib|%{_libdir}|g" %{buildroot}%{_sysconfdir}/gssapi_mech.conf

cat >%{buildroot}%{_sysconfdir}/exports <<EOF
# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
EOF

# manage documentation manually
install -d -m 755 %{buildroot}%{_docdir}/%{name}
install -m 644 README COPYING NEWS %{SOURCE6} \
    %{buildroot}%{_docdir}/%{name}

# fix perms
chmod 0755 %{buildroot}%{_bindir}/mount.nfs

mkdir -p %{buildroot}%{_sysusersdir}
cat >%{buildroot}%{_sysusersdir}/rpcuser.conf <<EOF
u rpcuser - "NFS RPC User" %{_localstatedir}/lib/nfs %{_bindir}/false
EOF

%files -n %{libname}
%{_libdir}/libnfsidmap.so.%{major}*
%{_libdir}/libnfsidmap

%files -n %{devname}
%{_libdir}/libnfsidmap.so
%{_includedir}/nfsidmap*.h
%{_libdir}/pkgconfig/libnfsidmap.pc
%{_mandir}/man3/*

%files
%{_sysusersdir}/rpcuser.conf
%{_docdir}/%{name}
%dir %{_localstatedir}/lib/nfs
%dir %{_localstatedir}/lib/nfs/v4recovery
%dir %{_localstatedir}/lib/nfs/rpc_pipefs
%dir %{_sysconfdir}/exports.d
%dir %attr(700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd
%dir %attr(700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd/sm
%dir %attr(700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd/sm.bak
%config(noreplace) %attr(644,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd/state
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
%dir %{_prefix}/lib/%{name}
%dir %{_prefix}/lib/%{name}/scripts
%{_prefix}/lib/%{name}/scripts/*
%{_sbindir}/nfsdctl
%{_sbindir}/nfsddebug
%{_sbindir}/rpc.statd
%{_sbindir}/mount.nfs
%{_sbindir}/mount.nfs4
%{_sbindir}/umount.nfs
%{_sbindir}/umount.nfs4
%{_sbindir}/rpcdebug
%{_sbindir}/nfsdebug
%{_sbindir}/fsidd
%{_prefix}/lib/udev/rules.d/60-nfs.rules
%{_prefix}/lib/systemd/system-generators/nfs-server-generator
%{_prefix}/lib/systemd/system-generators/rpc-pipefs-generator
%{_sbindir}/exportfs
%{_sbindir}/rpc.mountd
%{_sbindir}/rpc.nfsd
%{_sbindir}/sm-notify
%{_sbindir}/start-statd
%{_sbindir}/showmount
%{_sbindir}/mountstats
%{_sbindir}/nfsdcld
%{_sbindir}/nfsiostat
%{_sbindir}/nfsidmap
%{_sbindir}/blkmapd
%{_sbindir}/nfsstat
%{_sbindir}/nfsconf
%{_sbindir}/rpc.idmapd
%{_sbindir}/rpc.gssd
%{_sbindir}/nfsdclddb
%{_sbindir}/nfsdclnts
%{_bindir}/nfsref
%{_mandir}/man5/*
%{_mandir}/man7/*
%{_mandir}/man8/exportfs.8*
%{_mandir}/man8/nfsconf.8*
%{_mandir}/man8/nfsdclddb.8*
%{_mandir}/man8/nfsdclnts.8*
%{_mandir}/man8/nfsref.8*
%{_mandir}/man8/mountd.8*
%{_mandir}/man8/nfsd.8*
%{_mandir}/man8/nfsdctl.8*
%{_mandir}/man8/rpc.mountd.8*
%{_mandir}/man8/rpc.nfsd.8*
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
%{_mandir}/man8/nfsiostat.8*
%{_mandir}/man8/nfsidmap.8*
%{_mandir}/man8/blkmapd.8*
%{_mandir}/man8/rpc.gssd.8*
%{_mandir}/man8/rpc.idmapd.8*
%{_mandir}/man8/gssd.8*
%{_mandir}/man8/idmapd.8*
%{_mandir}/man8/nfsdcld.8*
%{_bindir}/rpcctl
%{_prefix}/lib/udev/rules.d/99-nfs.rules
%{_libexecdir}/nfsrahead
%{_mandir}/man8/rpcctl.8*
