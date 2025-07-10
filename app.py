import streamlit as st
import sqlite3
import pandas as pd

DB_FILENAME = "tennis.db"
PLAYERS = [
    "Felipe", "Victor", "Bruno", "Marcelo", "Willyan",
    "Vinicius", "Hesaú", "Pedro", "Carlos"
]

def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            player1 TEXT,
            player2 TEXT,
            set1_p1 INTEGER,
            set1_p2 INTEGER,
            set2_p1 INTEGER,
            set2_p2 INTEGER,
            set3_p1 INTEGER,
            set3_p2 INTEGER,
            played INTEGER DEFAULT 0
        )
    ''')
    c.execute('SELECT COUNT(*) FROM matches')
    if c.fetchone()[0] == 0:
        for i in range(len(PLAYERS)):
            for j in range(i+1, len(PLAYERS)):
                c.execute(
                    'INSERT INTO matches (player1, player2) VALUES (?, ?)',
                    (PLAYERS[i], PLAYERS[j])
                )
    conn.commit()
    conn.close()

def compute_ranking():
    conn = sqlite3.connect(DB_FILENAME)
    df = pd.read_sql_query('SELECT * FROM matches', conn)
    conn.close()

    stats = []
    for p in PLAYERS:
        m = df[(df.player1 == p) | (df.player2 == p)]
        played = int(m.played.sum())
        points = tie_wins = tie_losses = 0
        for _, r in m.iterrows():
            if r.played == 1:
                sets = [(r.set1_p1, r.set1_p2), (r.set2_p1, r.set2_p2)]
                if r.set3_p1 is not None:
                    sets.append((r.set3_p1, r.set3_p2))
                wins1 = sum(1 for a,b in sets if a>b)
                wins2 = sum(1 for a,b in sets if b>a)
                if p == r.player1:
                    tie_wins += sum(1 for a,b in sets if a>b)
                    tie_losses += sum(1 for a,b in sets if a<b)
                else:
                    tie_wins += sum(1 for a,b in sets if b>a)
                    tie_losses += sum(1 for a,b in sets if b<a)
                if (p == r.player1 and wins1>wins2) or (p == r.player2 and wins2>wins1):
                    points += 1
        stats.append({'player': p, 'played': played, 'points': points, 'tie_diff': tie_wins - tie_losses})

    df_stats = pd.DataFrame(stats).sort_values(['points','tie_diff'], ascending=[False,False]).reset_index(drop=True)

    # desempate direto entre dois
    for pts, grp in df_stats.groupby('points'):
        if len(grp)==2:
            p1, p2 = grp.player.tolist()
            row = df[((df.player1==p1)&(df.player2==p2))|((df.player1==p2)&(df.player2==p1))]
            if not row.empty and row.iloc[0].played==1:
                r = row.iloc[0]
                sets=[(r.set1_p1,r.set1_p2),(r.set2_p1,r.set2_p2)]
                if r.set3_p1 is not None:
                    sets.append((r.set3_p1,r.set3_p2))
                wins1=sum(1 for a,b in sets if a>b)
                wins2=sum(1 for a,b in sets if b>a)
                winner = r.player1 if wins1>wins2 else r.player2
                idx1 = df_stats.index[df_stats.player==p1][0]
                idx2 = df_stats.index[df_stats.player==p2][0]
                if (winner==p2 and idx1<idx2) or (winner==p1 and idx2<idx1):
                    df_stats.iloc[[idx1,idx2]] = df_stats.iloc[[idx2,idx1]].values

    return df_stats

def main():
    st.title("Torneio - Amigos do Tennis")
    init_db()
    menu = st.sidebar.radio("Navegação", ["Registrar Resultado","Jogos","Ranking"])

    if menu=="Registrar Resultado":
        conn = sqlite3.connect(DB_FILENAME)
        df = pd.read_sql_query('SELECT * FROM matches WHERE played=0', conn)
        conn.close()
        if df.empty:
            st.info("Não há partidas pendentes.")
        else:
            df['match'] = df.player1+" vs "+df.player2
            sel = st.selectbox("Escolha a partida:", df.match)
            row = df[df.match==sel].iloc[0]
            s1p1 = st.number_input(f"{row.player1} (Tie 1)",0,20,key="s1p1")
            s1p2 = st.number_input(f"{row.player2} (Tie 1)",0,20,key="s1p2")
            s2p1 = st.number_input(f"{row.player1} (Tie 2)",0,20,key="s2p1")
            s2p2 = st.number_input(f"{row.player2} (Tie 2)",0,20,key="s2p2")
            use3 = st.checkbox("Tie-break 3?")
            if use3:
                s3p1 = st.number_input(f"{row.player1} (Tie 3)",0,20,key="s3p1")
                s3p2 = st.number_input(f"{row.player2} (Tie 3)",0,20,key="s3p2")
            else:
                s3p1=s3p2=None
            if st.button("Registrar"):
                conn=sqlite3.connect(DB_FILENAME)
                c=conn.cursor()
                c.execute('''
                    UPDATE matches SET
                      set1_p1=?, set1_p2=?, set2_p1=?, set2_p2=?,
                      set3_p1=?, set3_p2=?, played=1
                    WHERE id=?
                ''', (s1p1,s1p2,s2p1,s2p2,s3p1,s3p2,row.id))
                conn.commit(); conn.close()
                st.success("Resultado registrado!")
    elif menu=="Jogos":
        conn=sqlite3.connect(DB_FILENAME)
        df=pd.read_sql_query('SELECT * FROM matches',conn); conn.close()
        if st.checkbox("Pendentes", True):
            st.write("### Jogos Pendentes")
            st.dataframe(df[df.played==0][['player1','player2']])
        if st.checkbox("Disputados", True):
            d=df[df.played==1].copy()
            d['Placar'] = d.apply(lambda r: f"{r.set1_p1}–{r.set1_p2}, {r.set2_p1}–{r.set2_p2}" + (f", {r.set3_p1}–{r.set3_p2}" if r.set3_p1 is not None else ""), axis=1)
            st.write("### Jogos Disputados")
            st.dataframe(d[['player1','player2','Placar']])
    else:
        df_stats=compute_ranking()
        df_stats.index += 1
        st.write("### Ranking Geral")
        st.dataframe(df_stats.rename_axis("Posição").reset_index())

if __name__=="__main__":
    main()
