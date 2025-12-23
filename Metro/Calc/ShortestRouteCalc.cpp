#include <bits/stdc++.h>
#define ll long long
using namespace std;
ll T,N[30],k,graph[30][50],g[1005][1005];
string s,mp2[505],ss;
map <string,ll> mp;
int main()
{
	freopen("NameList.txt","r",stdin);
	freopen("test.csv","w",stdout);
	scanf("%lld",&T);
	cerr<<T<<endl;
	memset(g,0x3f,sizeof(g));
	for(int i=0;i<1005;i++)
		g[i][i]=0;
	for(int i=1;i<=T;i++)
	{
		cin>>s;
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
			if(j>1)
			{
				if(i==25) cerr<<s<<" "<<mp[s]<<" "<<ss<<" "<<mp[ss]<<endl;
				g[mp[s]][mp[ss]]=g[mp[ss]][mp[s]]=1;
				if(i==25) cerr<<g[mp[ss]][mp[s]]<<endl;
			}
			
			graph[i][j]=mp[s];
		}
	}
	for(int i=1;i<=T;i++)
	{
		for(int j=1;j<=N[i];j++)
			cerr<<mp2[graph[i][j]]<<" ";
		cerr<<"\n";
	}
	ll n=k;
	for (int k = 1; k <= n; k++)
		for (int x = 1; x <= n; x++)
			for (int y = 1; y <= n; y++)
				g[x][y] = min(g[x][y], g[x][k] + g[k][y]);
	cout<<" ,";
	for(int i=1;i<=n;i++)
	{
		if(i==n) cout<<mp2[i]<<"\n";
		else cout<<mp2[i]<<",";
	}
	for(int i=1;i<=n;i++)
	{
		cout<<mp2[i]<<",";
		for(int j=1;j<=n;j++)
		{
			if(j==n) printf("%lld\n",g[i][j]);
			else printf("%lld,",g[i][j]);
		}
	}
		
	return 0;
}
