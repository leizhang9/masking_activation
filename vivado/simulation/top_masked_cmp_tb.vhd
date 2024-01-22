library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity top_masked_cmp_tb is
end entity;

architecture arch of top_masked_cmp_tb is

  signal clk : std_logic := '0';
  signal rst : std_logic;

  signal parity_error : std_logic;
  signal frame_error : std_logic;
  signal uart_rx : std_logic;
  signal uart_tx : std_logic;
  signal led_idle : std_logic;
  signal trigger : std_logic;

  signal uart_clk : std_logic := '0';

  signal clk_uart : std_logic := '0';


  constant clk_period : time := 1000 ns;
  constant uart_clk_period : time := ((1000000000 / 921600) / 2) * 1 ns;

  component top_masked_cmp is
    port (
    clk_slow : in std_logic;
    clk_fast : in std_logic;
    rst : in std_logic;

    parity_error : out std_logic;
    frame_error : out std_logic;
    uart_rx : in std_logic;
    uart_tx : out std_logic;
    led_idle : out std_logic;

    trigger : out std_logic
  );
  end component;

  procedure tx_byte_p (constant byte : in  std_ulogic_vector(7 downto 0);
                     signal uart_rxd_o : out std_ulogic) is
      variable i : integer;
  begin
      report "start tx_byte_p" severity note;

      wait until rising_edge(uart_clk);
      --start bit 0
      uart_rxd_o <= '0';
      wait until rising_edge(uart_clk);
      --data bits
      for i in 0 to 7 loop
        uart_rxd_o <= byte(i);
        wait until rising_edge(uart_clk);
      end loop;
      --parity even
      uart_rxd_o <= byte(7) xor byte(6) xor byte(5) xor byte(4) xor
                     byte(3) xor byte(2) xor byte(1) xor byte(0);
      wait until rising_edge(uart_clk);
      --stop bit 1
      uart_rxd_o <= '1';
      wait until rising_edge(uart_clk);

      report "end tx_byte_p" severity note;
  end tx_byte_p;


begin

  uart_clk <= not uart_clk after uart_clk_period;
  clk <= not clk after clk_period / 2;
  clk_uart <= not clk_uart after 5 ns;

  dut : top_masked_cmp
  port map (
    clk_slow => clk,
    clk_fast => clk_uart,
    rst => rst,
    parity_error => parity_error,
    frame_error => frame_error,
    uart_rx => uart_rx,
    uart_tx => uart_tx,
    led_idle => led_idle,
    trigger => trigger
  );

  stim : process is
  begin
    rst <= '0';
    wait for 10*clk_period;
    rst <= '1';
    wait for 10*clk_period;

    tx_byte_p(x"01", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"04", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"14", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"50", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"51", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"3c", uart_rxd_o => uart_rx);
    wait for 10*uart_clk_period;

    tx_byte_p(x"02", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"12", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    rand_loop : for i in 0 to 17 loop
      tx_byte_p(std_ulogic_vector(to_unsigned(i, 8)), uart_rxd_o => uart_rx);
      wait for uart_clk_period;
    end loop;
    wait for 10*uart_clk_period;

    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;

    wait for 5ms;

    tx_byte_p(x"01", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"04", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"07", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"0a", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"d5", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"32", uart_rxd_o => uart_rx);
    wait for uart_clk_period;

    tx_byte_p(x"02", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"12", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    rand_loop1 : for i in 0 to 17 loop
      tx_byte_p(std_ulogic_vector(to_unsigned(i+100, 8)), uart_rxd_o => uart_rx);
      wait for uart_clk_period;
    end loop;
    wait for 10*uart_clk_period;

    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;

    wait;
  end process;

end architecture;
