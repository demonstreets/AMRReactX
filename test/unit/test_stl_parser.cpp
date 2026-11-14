#include "stl_parser.H"
#include <cmath>
#include <fstream>
#include <iostream>
#include <filesystem>
static int nf=0;
void chk(bool c,const std::string& m){if(!c){std::cerr<<"FAIL:"<<m<<"\n";nf++;}else std::cout<<"PASS:"<<m<<"\n";}
int main(){
    const auto stl_path = (std::filesystem::temp_directory_path() / "codex_test_tet.stl").string();
    std::ofstream o(stl_path);
    o<<"solid t\n  facet normal 0 0 -1\n    outer loop\n      vertex 0 0 0\n      vertex 1 0 0\n      vertex 0 1 0\n    endloop\n  endfacet\n";
    o<<"  facet normal -1 0 0\n    outer loop\n      vertex 0 0 0\n      vertex 0 1 0\n      vertex 0 0 1\n    endloop\n  endfacet\n";
    o<<"  facet normal 0 -1 0\n    outer loop\n      vertex 0 0 0\n      vertex 0 0 1\n      vertex 1 0 0\n    endloop\n  endfacet\n";
    o<<"  facet normal 0.57735 0.57735 0.57735\n    outer loop\n      vertex 1 0 0\n      vertex 0 1 0\n      vertex 0 0 1\n    endloop\n  endfacet\n";
    o<<"endsolid t\n";o.close();
    pele::STLReader r;r.read(stl_path);
    auto& f=r.getFacets();
    chk(f.size()==4,"4 facets");
    for(size_t i=0;i<f.size();i++){
        double l=std::sqrt(f[i].normal[0]*f[i].normal[0]+f[i].normal[1]*f[i].normal[1]+f[i].normal[2]*f[i].normal[2]);
        chk(std::abs(l-1.0)<1e-4,"normal "+std::to_string(i));
    }
    chk(f[0].vertices[0][2]==0.0,"Face0 z=0");
    std::cout<<"\n==="<<(nf==0?"ALL PASS":"FAIL")<<"===\n";
    return nf?1:0;
}