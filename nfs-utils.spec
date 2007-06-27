%define build_nfsv4 1
%define build_wrap 1

# commandline overrides:
# rpm -ba|--rebuild --with 'xxx'
%{?_without_nfsv4:	%global build_nfsv4 0}
%{?_with_nfsv4:		%global build_nfsv4 1}
%{?_without_wrap:	%global build_wrap 0}
%{?_with_wrap:		%global build_wrap 1}

Name:		nfs-utils
Epoch:		1
Version:	1.1.0
Release:	%mkrel 1
Summary:	The utilities for Linux NFS server
Group:		Networking/Other
License:	GPL
URL:		http://sourceforge.net/projects/nfs/
Source0:	http://prdownloads.sourceforge.net/nfs/%{name}-%{version}.tar.gz
Source1:	ftp://nfs.sourceforge.net/pub/nfs/nfs.doc.tar.bz2
Source2:	nfs.init
Source3:	nfs.sysconfig
Source4:	nfslock.init
Source5:	nfsv4.schema
Source6:	rpcgssd.init
Source7:	rpcidmapd.init
Source8:	rpcsvcgssd.init
Source9:	gssapi_mech.conf
Source10:	idmapd.conf
Patch1:		eepro-support.patch
# Local Patches (FC)
Patch51:	nfs-utils-1.0.6-mountd.patch
Patch52:	nfs-utils-1.0.6-idmap.conf.patch
Patch54:	nfs-utils-1.0.7-mountd-stat64.patch
# NFS4 patches
Patch101:   nfs-utils-1.1.0-001-memory-leak-in-mountd.dif
Patch102:   nfs-utils-1.1.0-002-mount-nfs-nfsv4-mounts-give.dif
Patch103:   nfs-utils-1.1.0-003-gssd_fix_usage_message.dif
Patch104:   nfs-utils-1.1.0-004-mount_fix_compiler_warning.dif
Patch105:   nfs-utils-1.1.0-005-nfslib_move_pseudoflavor_to_common_location.dif
Patch106:   nfs-utils-1.1.0-006-libnfs_add_secinfo_support.dif
Requires:	nfs-utils-clients
Requires:	rpcbind
# needed because of /etc/exports transfer
Conflicts:	setup < 2.7.8
Conflicts:	clusternfs
Requires(post): rpm-helper
Requires(preun): rpm-helper
BuildRequires:	automake1.7
BuildRequires:	autoconf2.5
BuildRequires:	pkgconfig
BuildRequires:	libtool
%if %{build_nfsv4}
Requires:	    kernel >= 2.6.0
BuildRequires:	krb5-devel >= 1.3
BuildRequires:	libevent-devel
BuildRequires:	nfsidmap-devel >= 0.16
BuildRequires:	gssapi-devel >= 0.9
BuildRequires:	rpcsecgss-devel >= 0.12
%endif
%if %{build_wrap}
Requires:	    tcp_wrappers
BuildRequires:	tcp_wrappers-devel
%endif
Buildroot:	%{_tmppath}/%{name}-%{version}

%description
The nfs-utils package provides a daemon for the kernel NFS server
and related tools, which provides a much higher level of
performance than the traditional Linux NFS server used by most
users.

This package also contains the showmount program. Showmount
queries the mount daemon on a remote host for information about
the NFS (Network File System) server on the remote host. For
example, showmount can display the clients which are mounted on
that host.

The following are valid build options.

(ie. use with rpm --rebuild):

    --without nfsv4	Build with NFS protocol v4 support
    --without wrap	Build with tcp_wrappers support

%package	clients
Summary:	The utilities for Linux NFS client
Group:		Networking/Other
Requires:	rpcbind
%if %{build_nfsv4}
Requires:	kernel >= 2.6.0
# needed because of service scripts transfer
Conflicts:  nfs-utils <= 1:1.0.12-2mdv2007.1
%endif
Requires(pre): rpm-helper
Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires(postun): rpm-helper

%description	clients
The nfs-utils package provides a daemon for the kernel NFS server
and related tools, which provides a much higher level of
performance than the traditional Linux NFS server used by most
users.

This package also contains the showmount program. Showmount
queries the mount daemon on a remote host for information about
the NFS (Network File System) server on the remote host. For
example, showmount can display the clients which are mounted on
that host.

%prep
%setup -q -a1 -n %{name}-%{version}

mkdir -p Mandriva
cp %{SOURCE2} Mandriva/nfs.init
cp %{SOURCE3} Mandriva/nfs.sysconfig
cp %{SOURCE4} Mandriva/nfslock.init
cp %{SOURCE5} Mandriva/nfsv4.schema
cp %{SOURCE6} Mandriva/rpcgssd.init
cp %{SOURCE7} Mandriva/rpcidmapd.init
cp %{SOURCE8} Mandriva/rpcsvcgssd.init
cp %{SOURCE9} Mandriva/gssapi_mech.conf
cp %{SOURCE10} Mandriva/idmapd.conf

# fix strange perms
find . -type d -perm 0700 -exec chmod 755 {} \;
find . -type f -perm 0555 -exec chmod 755 {} \;
find . -type f -perm 0444 -exec chmod 644 {} \;

%patch1 -p1 -b .eepro-support
%patch51 -p1 -b .mountd
%patch52 -p1 -b .conf
%patch54 -p1 -b .stat64

%if %{build_nfsv4}
%patch101 -p1 -b .memory-leak-in-mountd
%patch102 -p1 -b .mount-nfs-nfsv4-mounts-give
%patch103 -p1 -b .gssd_fix_usage_message
%patch104 -p1 -b .mount_fix_compiler_warning
%patch105 -p1 -b .nfslib_move_pseudoflavor_to_common_location
%patch106 -p1 -b .libnfs_add_secinfo_support.dif
%endif

# lib64 fixes
perl -pi -e "s|/usr/lib|%{_libdir}|g" Mandriva/*
perl -pi -e "s|\\$dir/lib/|\\$dir/%{_lib}/|g" configure

%if ! %{build_wrap}
# nuke tcp_wrappers
find . -type f | xargs perl -pi -e "s|\-DHAVE_TCP_WRAPPER||g"
find . -type f | xargs perl -pi -e "s|\-lwrap||g"
%endif
	
%build
%serverbuild
sh autogen.sh
%configure2_5x \
    --with-statedir=%{_localstatedir}/nfs \
    --with-statduser=rpcuser \
    --enable-nfsv3 \
%if %{build_nfsv4}
    --enable-nfsv4 \
    --enable-gss \
    --enable-secure-statd \
    --with-krb5=%{_prefix} \
%else
    --disable-nfsv4 \
    --disable-gss \
    --disable-secure-statd \
    --without-krb5 \
%endif
    --disable-rquotad

make all

%install
rm -rf %{buildroot}

# don't fiddle with the initscript!
export DONT_GPRINTIFY=1

install -d %{buildroot}{/sbin,/usr/sbin}
install -d %{buildroot}%{_mandir}/{man5,man8}
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_localstatedir}/nfs/statd
install -d %{buildroot}%{_localstatedir}/nfs/v4recovery

%make \
	DESTDIR=%{buildroot} \
	MANDIR=%{buildroot}%{_mandir} \
	SBINDIR=%{buildroot}%{_prefix}/sbin \
	install

install -m0755 tools/rpcdebug/rpcdebug %{buildroot}/sbin/
ln -snf rpcdebug %{buildroot}/sbin/nfsdebug
ln -snf rpcdebug %{buildroot}/sbin/nfsddebug

install -m0755 Mandriva/nfs.init %{buildroot}%{_initrddir}/nfs
install -m0755 Mandriva/nfslock.init %{buildroot}%{_initrddir}/nfslock
install -m0644 Mandriva/nfs.sysconfig %{buildroot}/etc/sysconfig/nfs

touch %{buildroot}%{_localstatedir}/nfs/rmtab
mv %{buildroot}%{_sbindir}/rpc.statd %{buildroot}/sbin/

%if %{build_nfsv4}
install -m0755 Mandriva/rpcidmapd.init %{buildroot}%{_initrddir}/rpcidmapd
install -m0755 Mandriva/rpcgssd.init %{buildroot}%{_initrddir}/rpcgssd
install -m0755 Mandriva/rpcsvcgssd.init %{buildroot}%{_initrddir}/rpcsvcgssd
install -m0644 Mandriva/idmapd.conf %{buildroot}%{_sysconfdir}/idmapd.conf
install -m0644 Mandriva/gssapi_mech.conf %{buildroot}%{_sysconfdir}/gssapi_mech.conf
install -d %{buildroot}%{_localstatedir}/nfs/rpc_pipefs
%endif

# nuke dupes
rm -f %{buildroot}%{_sbindir}/rpcdebug

cat >%{buildroot}%{_sysconfdir}/exports <<EOF
# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
EOF

cat > README.urpmi << EOF
NFS4 support
------------
This package supports NFS4. In order to use it on server side, you need to set
USE_NFS4 and optionally SECURE_NFS in /etc/sysconfig/nfs file, so as to have
the nfs service handle everything automatically. On client side, you need to
launch rpc.idmapd and optionally rpc.rpcgssd services manually.
EOF

%post
%_post_service nfs
%if %{build_nfsv4}
%_post_service rpcsvcgssd
%endif

%create_ghostfile %{_localstatedir}/nfs/xtab root root 644
%create_ghostfile %{_localstatedir}/nfs/etab root root 644
%create_ghostfile %{_localstatedir}/nfs/rmtab root root 644

%preun
%_preun_service nfs
%if %{build_nfsv4}
%_preun_service rpcsvcgssd
%endif

%pre clients
%_pre_useradd rpcuser %{_localstatedir}/nfs /bin/false

%post clients
%_post_service nfslock 
%if %{build_nfsv4}
%_post_service rpcidmapd
%_post_service rpcgssd
%endif

%preun clients
%_preun_service nfslock
%if %{build_nfsv4}
%_preun_service rpcidmapd
%_preun_service rpcgssd
%endif

%postun clients
%_postun_userdel rpcuser

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc README ChangeLog COPYING README.urpmi
%doc nfs/*.html nfs/*.ps linux-nfs
%{_initrddir}/nfs
%config(noreplace) %ghost %{_localstatedir}/nfs/xtab
%config(noreplace) %ghost %{_localstatedir}/nfs/etab
%config(noreplace) %ghost %{_localstatedir}/nfs/rmtab
%config(noreplace) %{_sysconfdir}/exports
/sbin/rpcdebug
/sbin/nfsdebug
/sbin/nfsddebug
%{_sbindir}/exportfs
%{_sbindir}/nfsstat
%{_sbindir}/rpc.mountd
%{_sbindir}/rpc.nfsd
%{_mandir}/man5/exports.5*
%{_mandir}/man7/nfsd.7*
%{_mandir}/man8/exportfs.8*
%{_mandir}/man8/mountd.8*
%{_mandir}/man8/nfsd.8*
%{_mandir}/man8/nfsstat.8*
%{_mandir}/man8/rpc.mountd.8*
%{_mandir}/man8/rpc.nfsd.8*
%if %{build_nfsv4}
%doc Mandriva/nfsv4.schema
%{_initrddir}/rpcsvcgssd
%{_sbindir}/rpc.svcgssd
%{_mandir}/man8/rpc.svcgssd.8*
%{_mandir}/man8/svcgssd.8*
%{_mandir}/man8/rpcdebug.8*
%endif

%files clients
%defattr(-,root,root)
%doc README
%config(noreplace) %{_sysconfdir}/sysconfig/nfs
%{_initrddir}/nfslock
/sbin/rpc.statd
/sbin/mount.nfs
/sbin/mount.nfs4
/sbin/umount.nfs
/sbin/umount.nfs4
%{_sbindir}/sm-notify
%{_sbindir}/start-statd
%{_sbindir}/showmount
%{_mandir}/man5/nfs.5*
%{_mandir}/man8/mount.nfs.8*
%{_mandir}/man8/rpc.sm-notify.8*
%{_mandir}/man8/sm-notify.8*
%{_mandir}/man8/umount.nfs.8*
%{_mandir}/man8/rpc.statd.8*
%{_mandir}/man8/statd.8*
%{_mandir}/man8/showmount.8*
%dir %{_localstatedir}/nfs
%dir %{_localstatedir}/nfs/v4recovery
%dir %{_localstatedir}/nfs/state
%dir %attr(0700,rpcuser,rpcuser) %{_localstatedir}/nfs/statd
%if %{build_nfsv4}
%config(noreplace) %{_sysconfdir}/idmapd.conf
%config(noreplace) %{_sysconfdir}/gssapi_mech.conf
%dir %{_localstatedir}/nfs/rpc_pipefs
%{_sbindir}/rpc.idmapd
%{_sbindir}/rpc.gssd
%{_sbindir}/gss_clnt_send_err
%{_sbindir}/gss_destroy_creds
%{_initrddir}/rpcidmapd
%{_initrddir}/rpcgssd
%{_mandir}/man5/idmapd.conf.5*
%{_mandir}/man8/rpc.gssd.8*
%{_mandir}/man8/rpc.idmapd.8*
%{_mandir}/man8/gssd.8*
%{_mandir}/man8/idmapd.8*
%endif
