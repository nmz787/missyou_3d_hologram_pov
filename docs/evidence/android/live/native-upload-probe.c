/* Analysis harness: call the unmodified APK ELF's exported uploader.
 * f_log is suppressed; sendto/recvfrom are logged and passed to kernel syscalls.
 * Only the explicitly named scratch file is uploaded. No JNI initialization.
 */
extern void *dlopen(const char *,int);
extern void *dlsym(void *,const char *);
extern char *dlerror(void);
extern int printf(const char *,...);
extern void exit(int);
extern int open(const char *,int,...);
extern long write(int,const void *,unsigned long);
extern long syscall(long,...);
static int capture=-1;
static void record(char direction,const void *data,unsigned length){
 unsigned char h[5]={direction,length,length>>8,length>>16,length>>24};
 write(capture,h,5);write(capture,data,length);
}
long sendto(int fd,const void *p,unsigned long n,int flags,const void *a,unsigned len){
 long r=syscall(206,fd,p,n,flags,a,len);if(r>0)record('S',p,(unsigned)r);return r;
}
long recvfrom(int fd,void *p,unsigned long n,int flags,void *a,unsigned *len){
 long r=syscall(207,fd,p,n,flags,a,len);if(r>0)record('R',p,(unsigned)r);return r;
}
void f_log(int a,int b,const char *tag,const char *fmt,...){(void)a;(void)b;(void)tag;(void)fmt;}
static void progress(void *context,unsigned value){printf("PROGRESS %u\n",value);}
static void result(void *a,void *b,unsigned status){printf("NATIVE_RESULT %u\n",status);}
void _start(void){
 capture=open("/data/local/tmp/povbin-native/upload-capture.dat",577,0600);
 void *lib=dlopen("/data/local/tmp/povbin-native/libSPCore.so",2);
 if(!lib){printf("LOAD ERROR: %s\n",dlerror());exit(1);}
 void (*upload)(char *,char *,void *,void *,void *,void *)=dlsym(lib,"old_dev_tcp_upload");
 upload("90USB.bin","/data/local/tmp/povbin-native/cd.bin",progress,result,0,0);
 exit(0);
}
