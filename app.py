import streamlit as st
import sqlite3
import pandas as pd

DB_FILENAME = "tennis.db"
# Lista de participantes: atualize aqui caso queira adicionar ou editar nomes
PLAYERS = [
    "Felipe",
    "Victor",
    "Bruno",
    "Marcelo",
    "Willyan",
    "Vinicius",
    "Hesaú",
    "Pedro",
    "Carlos",
    "Saulo"
]

# Inicializa o banco de dados e popula partidas (round robin)
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
    count = c.fetchone()[0]
    if count == 0:
        for i in range(len(PLAYERS)):
            for j in range(i+1, len(PLAYERS)):
                c.execute(
                    'INSERT INTO matches (player1, player2) VALUES (?, ?)',
                    (PLAYERS[i], PLAYERS[j])
                )
    conn.commit()
    conn.close()

# Calcula o ranking conforme regras definidas
def compute_ranking():
    conn = sqlite3.connect(DB_FILENAME)
    df = pd.read_sql_query('SELECT * FROM matches', conn)
    conn.close()

    stats = []
    for p in PLAYERS:
        m = df[(df['player1'] == p) | (df['player2'] == p)]
        played = int(m['played'].sum())
        points = 0
        tie_wins = 0
        tie_losses = 0
        for _, row in m.iterrows():
            if row['played'] == 1:
                sets = [
                    (row['set1_p1'], row['set1_p2']),
                    (row['set2_p1'], row['set2_p2'])
                ]
                if row['set3_p1'] is not None:
                    sets.append((row['set3_p1'], row['set3_p2']))
                wins1 = sum(1 for a, b in sets if a > b)
                wins2 = sum(1 for a, b in sets if b > a)
                # acumula tie-breaks
                if p == row['player1']:
                    tie_wins += sum(1 for a, b in sets if a > b)
                    tie_losses += sum(1 for a, b in sets if a < b)
                else:
                    tie_wins += sum(1 for a, b in sets if b > a)
                    tie_losses += sum(1 for a, b in sets if b < a)
                # pontua vitória
                if (p == row['player1'] and wins1 > wins2) or (p == row['player2'] and wins2 > wins1):
                    points += 1
        stats.append({'player': p, 'played': played, 'points': points, 'tie_diff': tie_wins - tie_losses})

    df_stats = pd.DataFrame(stats)
    df_stats = df_stats.sort_values(['points', 'tie_diff'], ascending=[False, False]).reset_index(drop=True)

    # desempate por confronto direto (apenas para duplo empate)
    for pts, group in df_stats.groupby('points'):
        if len(group) == 2:
            p1 = group.iloc[0]['player']
            p2 = group.iloc[1]['player']
            row = df[((df['player1'] == p1) & (df['player2'] == p2)) | ((df['player1'] == p2) & (df['player2'] == p1))]
            if not row.empty and row.iloc[0]['played'] == 1:
                r = row.iloc[0]
                sets = [(r['set1_p1'], r['set1_p2']), (r['set2_p1'], r['set2_p2'])]
                if r['set3_p1'] is not None:
                    sets.append((r['set3_p1'], r['set3_p2']))
                wins1 = sum(1 for a, b in sets if a > b)
                wins2 = sum(1 for a, b in sets if b > a)
                winner = r['player1'] if wins1 > wins2 else r['player2']
                idx1 = df_stats.index[df_stats['player'] == p1][0]
                idx2 = df_stats.index[df_stats['player'] == p2][0]
                if winner == p2 and idx1 < idx2:
                    df_stats.iloc[[idx1, idx2]] = df_stats.iloc[[idx2, idx1]].values
                if winner == p1 and idx2 < idx1:
                    df_stats.iloc[[idx1, idx2]] = df_stats.iloc[[idx2, idx1]].values

    return df_stats

# Função principal da UI Streamlit

def main():
    st.title("Torneio - Amigos do Tennis")
    init_db()
    menu = st.sidebar.radio("Navegação", ["Registrar Resultado", "Jogos", "Ranking"])

    if menu == "Registrar Resultado":
        conn = sqlite3.connect(DB_FILENAME)
        df = pd.read_sql_query('SELECT * FROM matches WHERE played = 0', conn)
        conn.close()
        if df.empty:
            st.info("Não há partidas pendentes.")
        else:
            df['match_str'] = df['player1'] + " vs " + df['player2']
            match = st.selectbox("Selecione a partida:", df['match_str'])
            sel = df[df['match_str'] == match].iloc[0]
            s1p1 = st.number_input(f"{sel['player1']} (Tie 1)", min_value=0, max_value=20, key="s1p1")
            s1p2 = st.number_input(f"{sel['player2']} (Tie 1)", min_value=0, max_value=20, key="s1p2")
            s2p1 = st.number_input(f"{sel['player1']} (Tie 2)", min_value=0, max_value=20, key="s2p1")
            s2p2 = st.number_input(f"{sel['player2']} (Tie 2)", min_value=0, max_value=20, key="s2p2")
            include_s3 = st.checkbox("Incluir Tie-break 3 (se necessário)")
            if include_s3:
                s3p1 = st.number_input(f"{sel['player1']} (Tie 3)", min_value=0, max_value=20, key="s3p1")
                s3p2 = st.number_input(f"{sel['player2']} (Tie 3)", min_value=0, max_value=20, key="s3p2")
            else:
                s3p1 = None
                s3p2 = None
            if st.button("Registrar Resultado"):
                conn = sqlite3.connect(DB_FILENAME)
                c = conn.cursor()
                c.execute('''
                    UPDATE matches SET
                        set1_p1=?, set1_p2=?, set2_p1=?, set2_p2=?, set3_p1=?, set3_p2=?, played=1
                    WHERE id=?
                ''', (s1p1, s1p2, s2p1, s2p2, s3p1, s3p2, sel['id']))
                conn.commit()
                conn.close()
                st.success("Resultado registrado com sucesso!")
    
    elif menu == "Jogos":
        conn = sqlite3.connect(DB_FILENAME)
        df = pd.read_sql_query('SELECT * FROM matches', conn)
        conn.close()
        if st.checkbox("Mostrar Pendentes", True):
            df_p = df[df['played'] == 0]
            st.write("### Jogos Pendentes")
            st.dataframe(df_p[['player1', 'player2']])
        if st.checkbox("Mostrar Disputados", True):
            df_d = df[df['played'] == 1]
            df_d['Placar'] = df_d.apply(
                lambda r: f"{r['set1_p1']}–{r['set1_p2']}, {r['set2_p1']}–{r['set2_p2']}" +
                          (f", {r['set3_p1']}–{r['set3_p2']}" if r['set3_p1'] is not None else ""),
                axis=1
            )
            st.write("### Jogos Disputados")
            st.dataframe(df_d[['player1', 'player2', 'Placar']])

    else:  # Ranking
        df_stats = compute_ranking()
        df_stats.index = df_stats.index + 1
        df_stats = df_stats.reset_index().rename(columns={'index': 'Posição'})
        st.write("### Ranking Geral")
        st.dataframe(df_stats[['Posição', 'player', 'played', 'points', 'tie_diff']].rename(
            columns={
                'player': 'Jogador', 'played': 'Disputados',
                'points': 'Vitórias', 'tie_diff': 'Saldo Tie-breaks'
            }
        ))

if __name__ == "__main__":
    main()
