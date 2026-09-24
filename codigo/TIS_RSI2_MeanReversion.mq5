//+------------------------------------------------------------------+
//|                          TIS_RSI2_MeanReversion_FINAL.mq5        |
//|                          Trade It Simple SENTINEL 2026            |
//|                          Fondo Sistematico Multiestrategia        |
//+------------------------------------------------------------------+
//========================================================
//  STATUS: LIVE (desplegado en producción)
// Entorno: MetaTrader 5 / Darwinex | ejecución automatizada
//  Version: 2.01  |  Last update: 2026-06-24
//========================================================
#property copyright "Trade It Simple 2026"
#property link      "https://www.tradeitsimplesolutions.com/"
#property version   "2.01"
#property description "RSI(2) MEAN REVERSION - VERSION DEFINITIVA"
#property description "Entry: RSI(2) < 15 + Close > SMA(200)"
#property description "Exit: 2 velas verdes consecutivas"
#property description "Risk Engine + Darwinex Zero Ready"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input group "====== ESTRATEGIA (VALIDADO - NO MODIFICAR) ======"
input int      InpRSIPeriod       = 2;           // Periodo RSI
input int      InpRSIThreshold    = 15;          // Umbral RSI entrada
input int      InpSMATrend        = 200;         // SMA Filtro de Tendencia

input group "====== MOTOR DE RIESGO ======"
input double   InpRiskPercent     = 1.0;         // % Riesgo por operacion
input double   InpMaxDailyDD      = 3.0;         // Kill switch diario %
input double   InpMaxTotalDD      = 8.0;         // Kill switch total % (D-Score)
input bool     InpUseATRSizing    = true;        // Position sizing por ATR?
input int      InpATRPeriod       = 14;          // Periodo ATR
input double   InpATRMultiple     = 2.0;         // Multiplicador ATR (virtual stop)

input group "====== EMERGENCIA Y MONITOREO ======"
input bool     InpEnableDailyKill  = true;       // Activar kill switch diario?
input bool     InpEnableTotalKill  = true;       // Activar kill switch total?
input bool     InpSendPushAlerts   = true;       // Notificaciones push?
input bool     InpSendEmailAlerts  = false;      // Alertas email?
input int      InpMagicNumber      = 100001;     // Magic Number (unico por EA)
input bool     InpShowDashboard    = true;       // Dashboard en chart?

CTrade         g_trade;
CPositionInfo  g_posInfo;

int            g_handleRSI;
int            g_handleSMA;
int            g_handleATR;

double         g_rsiBuffer[];
double         g_smaBuffer[];
double         g_atrBuffer[];

double         g_dayStartEquity;
double         g_peakEquity;
datetime       g_lastBarTime;
bool           g_dailyKillActive;
bool           g_totalKillActive;
string         g_killReason;

int            g_totalTrades;
int            g_wins;
int            g_losses;
double         g_grossProfit;
double         g_grossLoss;
double         g_maxDrawdownHit;

int OnInit()
{
   if(InpRSIThreshold < 5 || InpRSIThreshold > 30)
   {
      Print("RSI Threshold fuera de rango razonable (5-30)");
      return(INIT_PARAMETERS_INCORRECT);
   }

   if(InpRiskPercent < 0.1 || InpRiskPercent > 5.0)
   {
      Print("Risk % fuera de rango seguro (0.1-5.0)");
      return(INIT_PARAMETERS_INCORRECT);
   }

   g_handleRSI = iRSI(_Symbol, PERIOD_D1, InpRSIPeriod, PRICE_CLOSE);
   g_handleSMA = iMA(_Symbol, PERIOD_D1, InpSMATrend, 0, MODE_SMA, PRICE_CLOSE);
   g_handleATR = iATR(_Symbol, PERIOD_D1, InpATRPeriod);

   if(g_handleRSI == INVALID_HANDLE || g_handleSMA == INVALID_HANDLE || g_handleATR == INVALID_HANDLE)
   {
      Print("Error creando indicadores");
      return(INIT_FAILED);
   }

   ArraySetAsSeries(g_rsiBuffer, true);
   ArraySetAsSeries(g_smaBuffer, true);
   ArraySetAsSeries(g_atrBuffer, true);

   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(30);
   g_trade.SetTypeFilling(ORDER_FILLING_IOC);

   g_dayStartEquity  = AccountInfoDouble(ACCOUNT_EQUITY);
   g_peakEquity      = AccountInfoDouble(ACCOUNT_EQUITY);
   g_lastBarTime     = 0;
   g_dailyKillActive = false;
   g_totalKillActive = false;
   g_killReason      = "";
   g_maxDrawdownHit  = 0;

   g_totalTrades = 0;
   g_wins        = 0;
   g_losses      = 0;
   g_grossProfit = 0;
   g_grossLoss   = 0;

   Print("=== TIS RSI(2) MEAN REVERSION FINAL ===");
   Print("Simbolo: ", _Symbol);
   Print("Entrada: RSI(", InpRSIPeriod, ") < ", InpRSIThreshold, " + Close > SMA(", InpSMATrend, ")");
   Print("Salida: 2 Velas Verdes Consecutivas");
   Print("Riesgo: ", DoubleToString(InpRiskPercent, 1), "% por trade | ATRx", DoubleToString(InpATRMultiple, 1));
   Print("Kill Daily: ", InpMaxDailyDD, "% | Kill Total: ", InpMaxTotalDD, "%");
   Print("Magic: ", InpMagicNumber);

   Alert_TIS("EA INICIADO | " + _Symbol + " | RSI(" + IntegerToString(InpRSIPeriod) + ")<" +
             IntegerToString(InpRSIThreshold) + " | Exit: 2 Velas Verdes");

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   if(g_handleRSI != INVALID_HANDLE) IndicatorRelease(g_handleRSI);
   if(g_handleSMA != INVALID_HANDLE) IndicatorRelease(g_handleSMA);
   if(g_handleATR != INVALID_HANDLE) IndicatorRelease(g_handleATR);

   if(InpShowDashboard) ObjectsDeleteAll(0, "TIS_");

   Print("=== EA DETENIDO ===");
   Print("Trades: ", g_totalTrades, " | Wins: ", g_wins, " | Losses: ", g_losses);
   if(g_totalTrades > 0)
   {
      double wr = (double)g_wins / g_totalTrades * 100;
      Print("Win Rate: ", DoubleToString(wr, 1), "%");
      if(g_grossLoss > 0)
         Print("Profit Factor: ", DoubleToString(g_grossProfit / g_grossLoss, 2));
      Print("Max DD Hit: ", DoubleToString(g_maxDrawdownHit, 2), "%");
   }

   Alert_TIS("EA DETENIDO | Trades: " + IntegerToString(g_totalTrades) +
             " | W:" + IntegerToString(g_wins) + " L:" + IntegerToString(g_losses));
}

//+------------------------------------------------------------------+
//| OnTick                                                           |
//| FIX v2.01: El dashboard ahora se refresca en CADA tick para que |
//| refleje la posicion real en vivo. La logica de entrada/salida    |
//| sigue evaluandose solo al abrir una nueva vela diaria (sin cambio)|
//+------------------------------------------------------------------+
void OnTick()
{
   // El motor de riesgo (kill switch) se evalua en cada tick
   bool riskOK = RiskEngine();

   // Entrada/Salida: solo en vela diaria nueva (comportamiento original)
   if(riskOK && IsNewBar() && UpdateIndicators())
   {
      if(HasOpenPosition())
         CheckExit();

      if(!HasOpenPosition())
         CheckEntry();
   }

   // Dashboard: SIEMPRE, para reflejar la posicion real intradia
   if(InpShowDashboard)
      UpdateDashboard();
}

bool RiskEngine()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   if(equity > g_peakEquity)
      g_peakEquity = equity;

   MqlDateTime dt;
   TimeCurrent(dt);
   static int lastDay = -1;

   if(dt.day != lastDay)
   {
      lastDay = dt.day;
      g_dayStartEquity  = AccountInfoDouble(ACCOUNT_EQUITY);
      g_dailyKillActive = false;
      if(StringFind(g_killReason, "DIARIO") >= 0)
         g_killReason = "";
   }

   if(InpEnableDailyKill && g_dayStartEquity > 0)
   {
      double dailyDD = (g_dayStartEquity - equity) / g_dayStartEquity * 100.0;

      if(dailyDD >= InpMaxDailyDD && !g_dailyKillActive)
      {
         g_dailyKillActive = true;
         g_killReason = StringFormat("KILL DIARIO: -%.2f%% (limite %.1f%%)", dailyDD, InpMaxDailyDD);
         Print(g_killReason);
         Alert_TIS(g_killReason);
         EmergencyCloseAll("Kill Diario");
         return false;
      }

      if(g_dailyKillActive)
         return false;
   }

   if(InpEnableTotalKill && g_peakEquity > 0)
   {
      double totalDD = (g_peakEquity - equity) / g_peakEquity * 100.0;

      if(totalDD > g_maxDrawdownHit)
         g_maxDrawdownHit = totalDD;

      if(totalDD >= InpMaxTotalDD && !g_totalKillActive)
      {
         g_totalKillActive = true;
         g_killReason = StringFormat("KILL TOTAL: -%.2f%% (limite %.1f%%) - EA DETENIDO", totalDD, InpMaxTotalDD);
         Print(g_killReason);
         Alert_TIS(g_killReason);
         EmergencyCloseAll("Kill Total");
         return false;
      }

      if(g_totalKillActive)
         return false;
   }

   return true;
}

void EmergencyCloseAll(string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(g_posInfo.SelectByIndex(i))
      {
         if(g_posInfo.Symbol() == _Symbol && g_posInfo.Magic() == InpMagicNumber)
         {
            if(g_trade.PositionClose(g_posInfo.Ticket()))
               Print("CERRADA [", reason, "]: Ticket #", g_posInfo.Ticket());
            else
               Print("Error cerrando: ", g_trade.ResultRetcodeDescription());
         }
      }
   }
}

void CheckEntry()
{
   double close1 = iClose(_Symbol, PERIOD_D1, 1);

   if(close1 <= g_smaBuffer[1])
      return;

   if(g_rsiBuffer[1] >= InpRSIThreshold)
      return;

   double lots = CalculateLots();
   if(lots <= 0)
   {
      Print("Lot size = 0 - insuficiente margen o error calculo");
      return;
   }

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   string comment = StringFormat("TIS|RSI=%.0f|2GRN", g_rsiBuffer[1]);

   if(g_trade.Buy(lots, _Symbol, ask, 0, 0, comment))
   {
      g_totalTrades++;

      Print("=== ENTRY LONG - Trade #", g_totalTrades, " ===");
      Print("RSI(2) = ", DoubleToString(g_rsiBuffer[1], 1), " < ", InpRSIThreshold);
      Print("Close  = ", DoubleToString(close1, 2), " > SMA(200) = ", DoubleToString(g_smaBuffer[1], 2));
      Print("ATR    = ", DoubleToString(g_atrBuffer[1], 2));
      Print("Lots   = ", DoubleToString(lots, 2), " @ ", DoubleToString(ask, 2));
      Print("Exit: Esperando 2 velas verdes consecutivas");

      Alert_TIS(StringFormat("BUY %s | RSI=%.0f | Lots=%.2f | Esperando 2 velas verdes",
                _Symbol, g_rsiBuffer[1], lots));
   }
   else
   {
      Print("BUY FAILED: ", g_trade.ResultRetcodeDescription());
   }
}

void CheckExit()
{
   double close1 = iClose(_Symbol, PERIOD_D1, 1);
   double open1  = iOpen(_Symbol, PERIOD_D1, 1);
   double close2 = iClose(_Symbol, PERIOD_D1, 2);
   double open2  = iOpen(_Symbol, PERIOD_D1, 2);

   bool bar1_green = (close1 > open1);
   bool bar2_green = (close2 > open2);

   if(bar1_green && bar2_green)
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(!g_posInfo.SelectByIndex(i)) continue;
         if(g_posInfo.Symbol() != _Symbol) continue;
         if(g_posInfo.Magic() != InpMagicNumber) continue;
         if(g_posInfo.PositionType() != POSITION_TYPE_BUY) continue;

         double profit = g_posInfo.Profit() + g_posInfo.Swap() + g_posInfo.Commission();

         if(g_trade.PositionClose(g_posInfo.Ticket()))
         {
            if(profit >= 0)
            {
               g_wins++;
               g_grossProfit += profit;
            }
            else
            {
               g_losses++;
               g_grossLoss += MathAbs(profit);
            }

            double wr = g_totalTrades > 0 ? (double)g_wins / g_totalTrades * 100.0 : 0;
            double pf = g_grossLoss > 0 ? g_grossProfit / g_grossLoss : 99.99;
            string result = profit >= 0 ? "WIN" : "LOSS";

            Print("=== EXIT - 2 Velas Verdes - ", result, " ===");
            Print("P&L: $", DoubleToString(profit, 2));
            Print("Stats: ", g_wins, "W / ", g_losses, "L");
            Print("WR: ", DoubleToString(wr, 1), "% | PF: ", DoubleToString(pf, 2));

            Alert_TIS(StringFormat("%s EXIT %s | $%.0f | WR=%.0f%% | PF=%.2f | #%d",
                      result, _Symbol, profit, wr, pf, g_totalTrades));
         }
         else
         {
            Print("CLOSE FAILED: ", g_trade.ResultRetcodeDescription());
         }
      }
   }
}

double CalculateLots()
{
   double equity     = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmount = equity * InpRiskPercent / 100.0;

   double tickSize   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double lotStep    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double lotMin     = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lotMax     = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   if(tickSize == 0 || tickValue == 0)
   {
      Print("Error: Tick size o value = 0");
      return lotMin;
   }

   double stopDistance;
   if(InpUseATRSizing && g_atrBuffer[1] > 0)
      stopDistance = g_atrBuffer[1] * InpATRMultiple;
   else
      stopDistance = SymbolInfoDouble(_Symbol, SYMBOL_ASK) * 0.02;

   double stopTicks = stopDistance / tickSize;
   double lots = 0;

   if(stopTicks > 0 && tickValue > 0)
      lots = riskAmount / (stopTicks * tickValue);

   lots = MathFloor(lots / lotStep) * lotStep;
   lots = MathMax(lots, lotMin);
   lots = MathMin(lots, lotMax);

   double marginRequired;
   if(OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, lots, SymbolInfoDouble(_Symbol, SYMBOL_ASK), marginRequired))
   {
      double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      if(marginRequired > freeMargin * 0.8)
      {
         double reduction = (freeMargin * 0.8) / marginRequired;
         lots = MathFloor((lots * reduction) / lotStep) * lotStep;
         lots = MathMax(lots, lotMin);
         Print("Margen ajustado - Lots=", DoubleToString(lots, 2));
      }
   }

   return lots;
}

bool IsNewBar()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_D1, 0);
   if(currentBarTime == g_lastBarTime)
      return false;
   g_lastBarTime = currentBarTime;
   return true;
}

bool UpdateIndicators()
{
   if(CopyBuffer(g_handleRSI, 0, 0, 5, g_rsiBuffer) < 5) return false;
   if(CopyBuffer(g_handleSMA, 0, 0, 5, g_smaBuffer) < 5) return false;
   if(CopyBuffer(g_handleATR, 0, 0, 5, g_atrBuffer) < 5) return false;
   return true;
}

bool HasOpenPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(g_posInfo.SelectByIndex(i))
         if(g_posInfo.Symbol() == _Symbol && g_posInfo.Magic() == InpMagicNumber)
            return true;
   }
   return false;
}

int CountPositions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(g_posInfo.SelectByIndex(i))
         if(g_posInfo.Symbol() == _Symbol && g_posInfo.Magic() == InpMagicNumber)
            count++;
   }
   return count;
}

void Alert_TIS(string message)
{
   if(InpSendPushAlerts)  SendNotification(message);
   if(InpSendEmailAlerts) SendMail("TIS RSI2 FINAL", message);
}

void UpdateDashboard()
{
   // FIX v2.01: proteccion: no dibujar hasta que los indicadores tengan datos
   if(ArraySize(g_rsiBuffer) < 2 || ArraySize(g_smaBuffer) < 2) return;

   int x = 20, y = 30;
   int lineH = 18;

   DashLabel("TIS_H1", "TIS RSI(2) FINAL v2.01", x, y, clrDodgerBlue, 11);
   y += lineH + 2;
   DashLabel("TIS_H2", _Symbol + " D1 | Exit: 2 Velas Verdes", x, y, clrDarkGray, 9);
   y += lineH + 6;

   if(g_dailyKillActive || g_totalKillActive)
   {
      DashLabel("TIS_KILL", "KILL SWITCH ACTIVO - NO OPERA", x, y, clrRed, 11);
      y += lineH + 4;
   }
   else
   {
      DashLabel("TIS_KILL", "", x, y, clrBlack, 1);
   }

   double rsiVal = g_rsiBuffer[1];
   bool rsiSignal = (rsiVal < InpRSIThreshold);
   string rsiStr = StringFormat("RSI(2): %.1f %s", rsiVal, rsiSignal ? "<< SENAL" : "");
   DashLabel("TIS_RSI", rsiStr, x, y, rsiSignal ? clrLime : clrSilver, 10);
   y += lineH;

   double closeNow = iClose(_Symbol, PERIOD_D1, 0);
   bool aboveSMA = (closeNow > g_smaBuffer[0]);
   DashLabel("TIS_TRD", "SMA(200): " + (aboveSMA ? "ABOVE OK" : "BELOW X"),
             x, y, aboveSMA ? clrLime : clrOrangeRed, 10);
   y += lineH;

   double c1 = iClose(_Symbol, PERIOD_D1, 1);
   double o1 = iOpen(_Symbol, PERIOD_D1, 1);
   double c0 = iClose(_Symbol, PERIOD_D1, 0);
   double o0 = iOpen(_Symbol, PERIOD_D1, 0);
   int greens = 0;
   if(c1 > o1) greens++;
   if(c0 > o0) greens++;

   if(HasOpenPosition())
   {
      DashLabel("TIS_GRN", StringFormat("Velas verdes: %d/2 %s", greens, greens >= 2 ? "-> EXIT" : ""),
                x, y, greens >= 2 ? clrLime : clrYellow, 10);
   }
   else
   {
      DashLabel("TIS_GRN", "Sin posicion abierta", x, y, clrDarkGray, 9);
   }
   y += lineH + 6;

   if(HasOpenPosition())
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(g_posInfo.SelectByIndex(i) && g_posInfo.Symbol() == _Symbol && g_posInfo.Magic() == InpMagicNumber)
         {
            double pnl = g_posInfo.Profit() + g_posInfo.Swap() + g_posInfo.Commission();
            color pnlClr = pnl >= 0 ? clrLime : clrOrangeRed;
            DashLabel("TIS_POS", StringFormat("LONG %.2f lots | P&L: $%.0f", g_posInfo.Volume(), pnl),
                      x, y, pnlClr, 10);
            break;
         }
      }
   }
   else
   {
      DashLabel("TIS_POS", "FLAT - Esperando senal", x, y, clrGray, 9);
   }
   y += lineH + 6;

   DashLabel("TIS_ST1", StringFormat("Trades: %d | W: %d | L: %d",
             g_totalTrades, g_wins, g_losses), x, y, clrSilver, 9);
   y += lineH;

   if(g_totalTrades > 0)
   {
      double wr = (double)g_wins / g_totalTrades * 100;
      double pf = g_grossLoss > 0 ? g_grossProfit / g_grossLoss : 0;
      color wrClr = wr >= 60 ? clrLime : (wr >= 50 ? clrYellow : clrOrangeRed);
      DashLabel("TIS_ST2", StringFormat("WR: %.1f%% | PF: %.2f", wr, pf), x, y, wrClr, 9);
      y += lineH;
   }

   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double dailyDD = g_dayStartEquity > 0 ? (g_dayStartEquity - eq) / g_dayStartEquity * 100 : 0;
   double totalDD = g_peakEquity > 0 ? (g_peakEquity - eq) / g_peakEquity * 100 : 0;

   DashLabel("TIS_EQ", "Equity: $" + DoubleToString(eq, 0), x, y, clrWhite, 9);
   y += lineH;

   color ddClr = clrSilver;
   if(dailyDD > InpMaxDailyDD * 0.7 || totalDD > InpMaxTotalDD * 0.7) ddClr = clrOrangeRed;
   else if(dailyDD > InpMaxDailyDD * 0.5 || totalDD > InpMaxTotalDD * 0.5) ddClr = clrYellow;

   DashLabel("TIS_DD", StringFormat("DD: Day=%.1f%%/%.0f%% | Total=%.1f%%/%.0f%%",
             dailyDD, InpMaxDailyDD, totalDD, InpMaxTotalDD), x, y, ddClr, 9);
   y += lineH;

   DashLabel("TIS_MDD", StringFormat("Max DD hit: %.2f%%", g_maxDrawdownHit), x, y, clrDarkGray, 8);
}

void DashLabel(string name, string text, int x, int y, color clr, int fontSize)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   }
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
   ObjectSetString(0, name, OBJPROP_FONT, "Consolas");
}

double OnTester()
{
   double profit = TesterStatistics(STAT_PROFIT);
   double maxDD  = TesterStatistics(STAT_EQUITY_DD_RELATIVE);
   int    trades = (int)TesterStatistics(STAT_TRADES);

   if(maxDD == 0) return 0;

   double score = profit / maxDD;

   if(trades < 20)
      score *= (double)trades / 20.0;

   return score;
}
