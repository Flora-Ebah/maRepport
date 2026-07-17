-- =====================================================================
--  MA2E — Pilote Trésorerie & Reporting
--  Modèle de données canonique (léger) — PostgreSQL
--  Principe CDC conservé : identifiant MA2E propre, traçabilité de la
--  source, indépendance vis-à-vis de Perfect-Vision.
-- =====================================================================

-- ---------- Référentiel des comptes de trésorerie -------------------
-- Banques, caisses et coffre. Découplé du plan comptable Perfect-Vision.
CREATE TABLE IF NOT EXISTS dim_compte_tresorerie (
    id            SERIAL PRIMARY KEY,
    code          VARCHAR(30)  NOT NULL UNIQUE,   -- ECOBANK, UBA, JULAYA, COFFRE...
    libelle       VARCHAR(120) NOT NULL,
    type_compte   VARCHAR(20)  NOT NULL           -- BANQUE | CAISSE | COFFRE
                  CHECK (type_compte IN ('BANQUE','CAISSE','COFFRE')),
    actif         BOOLEAN      NOT NULL DEFAULT TRUE,
    cree_le       TIMESTAMP    NOT NULL DEFAULT now()
);

-- ---------- Fait : solde journalier (format long) -------------------
-- Une ligne par (jour, compte). Le format wide des fichiers Excel est
-- normalisé ici. On trace la source pour audit (BCEAO 7 ans).
CREATE TABLE IF NOT EXISTS fait_solde_journalier (
    id              BIGSERIAL PRIMARY KEY,
    date_jour       DATE        NOT NULL,
    compte_id       INTEGER     NOT NULL REFERENCES dim_compte_tresorerie(id),
    montant         NUMERIC(18,2) NOT NULL,
    -- Traçabilité source
    source_fichier  VARCHAR(200) NOT NULL,
    source_onglet   VARCHAR(80)  NOT NULL,
    source_ligne    INTEGER,
    -- Qualité de la donnée
    qualite_flag    VARCHAR(20)  NOT NULL DEFAULT 'OK'  -- OK | DATE_SUSPECTE | ECART_TOTAL
                    CHECK (qualite_flag IN ('OK','DATE_SUSPECTE','ECART_TOTAL','MONTANT_CORRIGE')),
    ingere_le       TIMESTAMP    NOT NULL DEFAULT now(),
    UNIQUE (date_jour, compte_id)
);
CREATE INDEX IF NOT EXISTS idx_solde_date  ON fait_solde_journalier (date_jour);
CREATE INDEX IF NOT EXISTS idx_solde_compte ON fait_solde_journalier (compte_id);

-- ---------- Référentiel des sociétés (reversements) ----------------
-- Employeurs dont les retenues sur salaire alimentent la mutuelle.
CREATE TABLE IF NOT EXISTS dim_societe (
    id        SERIAL PRIMARY KEY,
    code      VARCHAR(30)  NOT NULL UNIQUE,   -- CIE, SODECI, GS2E, SIVE...
    libelle   VARCHAR(120) NOT NULL,
    actif     BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------- Fait : reversement société (mensuel) -------------------
CREATE TABLE IF NOT EXISTS fait_reversement (
    id               BIGSERIAL PRIMARY KEY,
    periode          DATE         NOT NULL,          -- 1er du mois concerné
    societe_id       INTEGER      NOT NULL REFERENCES dim_societe(id),
    montant_retenu   NUMERIC(18,2),                  -- prélevé
    montant_reverse  NUMERIC(18,2),                  -- effectivement viré
    ecart            NUMERIC(18,2) GENERATED ALWAYS AS
                       (COALESCE(montant_retenu,0) - COALESCE(montant_reverse,0)) STORED,
    statut           VARCHAR(40),                    -- 'OK' | 'En attente de reversement'...
    source_fichier   VARCHAR(200),
    ingere_le        TIMESTAMP    NOT NULL DEFAULT now(),
    UNIQUE (periode, societe_id)
);

-- ---------- Vues de pilotage (alimentent les dashboards) -----------
-- Position de trésorerie consolidée par jour.
CREATE OR REPLACE VIEW v_tresorerie_jour AS
SELECT  f.date_jour,
        SUM(f.montant)                                              AS total_general,
        SUM(f.montant) FILTER (WHERE c.type_compte = 'BANQUE')      AS total_banques,
        SUM(f.montant) FILTER (WHERE c.type_compte = 'CAISSE')      AS total_caisses,
        SUM(f.montant) FILTER (WHERE c.type_compte = 'COFFRE')      AS total_coffre,
        COUNT(*)                                                    AS nb_comptes
FROM    fait_solde_journalier f
JOIN    dim_compte_tresorerie c ON c.id = f.compte_id
GROUP BY f.date_jour
ORDER BY f.date_jour;
