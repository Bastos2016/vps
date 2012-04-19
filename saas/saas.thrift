namespace py saas 

typedef i32 Ip 


struct Vps {
   1 : i32 id                        ,
   2 : optional Ip ipv4              ,
   3 : optional Ip ipv4_netmask      ,
   4 : optional Ip ipv4_gateway      ,
   5 : string password               ,
   6 : i32 os                        ,                       //os的id会软连接到真实的os镜像
   7 : i16 hd                        ,                       //单位G
   8 : i32 ram                       ,                       //单位M
   9 : i16 cpu                       ,                       //几个core
  10 : i32 host_id                   ,                       //如pc1.42qu.us
}

enum Cmd{
  NONE    = 0,
  OPEN    = 1,
  CLOSE   = 2,
  RESTART = 3,
}

struct Task {
    1:          Cmd   cmd = 0,
    2: optional i32   id
}

service VPS {

   Task  todo        ( 1:i32  host_id  ),
   void  done        ( 1:i32  host_id , 2:Task todo ),

   Vps   vps         ( 1:i32  vps_id   ),

}


