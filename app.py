import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Autenticação via JSON no repositório (sem usar oauth2client) ---
SVC_JSON  = "amigos-tennis-sheet-a5fb8ee01c0b.json"   # nome do seu JSON
SHEET_KEY = "1t23lrxm8H5f9bdR1q4QJ_Ow0tw8e5DS0vTy48iiKN74"  # ID da planilha

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds  = Credentials.from_service_account_file(SVC_JSON, scopes=scopes)
client = gspread.authorize(creds)
sheet  = client.open_by_key(SHEET_KEY).sheet1

@st.cache_data(ttl=300)
def load_matches():
    return pd.DataFrame(sheet.get_all_records())

def update_match(match_id, data):
    cell    = sheet.find(str(match_id), in_column=1)
    row_idx = cell.row
    headers = sheet.row_values(1)
    for k, v in data.items():
        if k in headers:
            col_idx = headers.index(k) + 1
            sheet.update_cell(row_idx, col_idx, v)

st.title("Torneio - Amigos do Tennis (Sheets)")
df = load_matches()
menu = st.sidebar.radio("Navegação", ["Registrar Resultado","Jogos","Ranking"])

if menu=="Registrar Resultado":
    pending = df[df.played==0]
    if pending.empty:
        st.info("Não há partidas pendentes.")
    else:
        pending["match"] = pending.player1 + " vs " + pending.player2
        sel = st.selectbox("Selecione:", pending["match"])
        row = pending[pending.match==sel].iloc[0]
        mid = row.id
        s1p1 = st.number_input(f"{row.player1} Tie 1",0,20,key="s1p1")
        s1p2 = st.number_input(f"{row.player2} Tie 1",0,20,key="s1p2")
        s2p1 = st.number_input(f"{row.player1} Tie 2",0,20,key="s2p1")
        s2p2 = st.number_input(f"{row.player2} Tie 2",0,20,key="s2p2")
        use3 = st.checkbox("Tie 3?")
        if use3:
            s3p1 = st.number_input(f"{row.player1} Tie 3",0,20,key="s3p1")
            s3p2 = st.number_input(f"{row.player2} Tie 3",0,20,key="s3p2")
        else:
            s3p1=s3p2=""
        if st.button("Registrar"):
            update_match(mid, {
                "set1_p1": s1p1, "set1_p2": s1p2,
                "set2_p1": s2p1, "set2_p2": s2p2,
                "set3_p1": s3p1, "set3_p2": s3p2,
                "played": 1
            })
            st.success("Registrado!")
            st.cache_data.clear()

elif menu=="Jogos":
    if st.checkbox("Pendentes", True):
        st.dataframe(df[df.played==0][["player1","player2"]])
    if st.checkbox("Disputados", True):
        d = df[df.played==1].copy()
        d["Placar"]=d.apply(
            lambda r: f"{r.set1_p1}–{r.set1_p2}, {r.set2_p1}–{r.set2_p2}"
                      + (f", {r.set3_p1}–{r.set3_p2}" if r.set3_p1!="" else ""),
            axis=1
        )
        st.dataframe(d[["player1","player2","Placar"]])

else:
    def compute(df):
        stats=[]
        players=sorted(pd.unique(df[['player1','player2']].values.ravel()))
        for p in players:
            m=df[(df.player1==p)|(df.player2==p)]
            pts=tw=tl=0
            played=int((m.played==1).sum())
            for _,r in m.iterrows():
                if r.played==1:
                    sets=[(r.set1_p1,r.set1_p2),(r.set2_p1,r.set2_p2)]
                    if r.set3_p1!="": sets.append((r.set3_p1,r.set3_p2))
                    w1=sum(1 for a,b in sets if a>b); w2=sum(1 for a,b in sets if b>a)
                    if (p==r.player1 and w1>w2) or (p==r.player2 and w2>w1): pts+=1
                    if p==r.player1:
                        tw+=sum(1 for a,b in sets if a>b); tl+=sum(1 for a,b in sets if a<b)
                    else:
                        tw+=sum(1 for a,b in sets if b>a); tl+=sum(1 for a,b in sets if b<a)
            stats.append({"player":p,"played":played,"points":pts,"tie_diff":tw-tl})
        df_s=pd.DataFrame(stats).sort_values(["points","tie_diff"],ascending=False).reset_index(drop=True)
        df_s.index+=1
        return df_s
    st.dataframe(compute(df).rename_axis("Posição").reset_index())
