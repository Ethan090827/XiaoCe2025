#include <bits/stdc++.h>
#define ll long long
using namespace std;
ll T,N[30],k,graph[30][50],g[1005][1005],n;
string s,mp2[505],ss,mpline2[505];
map <string,ll> mp,mpline;
vector <ll> station[505];
int main()
{
	freopen("NameList copy.txt","r",stdin);
	freopen("MinimumChange.csv","w",stdout);
	scanf("%lld",&T);
	cerr<<T<<endl;
	memset(g,0x3f,sizeof(g));
	for(int i=0;i<1005;i++)
		g[i][i]=0;
	for(int i=1;i<=T;i++)
	{
		cin>>s;
        mpline[s]=i;
        mpline2[i]=s;
		scanf("%lld",&N[i]);
		for(int j=1;j<=N[i];j++)
		{
			ss=s;
			cin>>s;
			if(mp.find(s)==mp.end())
			{
				mp[s]=++k;
				mp2[k]=s;
			}
			else
                for(int k:station[mp[s]])
                    g[k][i]=g[i][k]=1;
            station[mp[s]].push_back(i);
		}
	}
	for(int i=1;i<=T;i++)
	{
		for(int j=1;j<=N[i];j++)
			cerr<<mp2[graph[i][j]]<<" ";
		cerr<<"\n";
	}
    n=T;
	for (int k = 1; k <= n; k++)
		for (int x = 1; x <= n; x++)
			for (int y = 1; y <= n; y++)
				g[x][y] = min(g[x][y], g[x][k] + g[k][y]);
	n=k;
	cout<<" ,";
	for(int i=1;i<=n;i++)
	{
		if(i==n) cout<<mp2[i]<<"\n";
		else cout<<mp2[i]<<",";
	}
	n=k;
	for(int i=1;i<=n;i++)
	{
		cout<<mp2[i]<<",";
		for(int j=1;j<=n;j++)
		{
            ll dis=1<<30;
            for(int m:station[i])
                for(int n:station[j])
                    dis=min(dis,g[m][n]);
			if(j==n) printf("%lld\n",dis);
			else printf("%lld,",dis);
		}
	}
	return 0;
}
