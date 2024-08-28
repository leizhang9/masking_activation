library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity top_cw305_tb is
end entity;

architecture arch of top_cw305_tb is

  constant clk_period : time := 10 ns;
  constant uart_clk_period : time := 1120 ns;

  signal clk            : std_logic := '0';
  signal uart_clk       : std_logic := '0';
  signal rst            : std_logic;
  signal uart_rx        : std_logic := '1';
  signal uart_tx        : std_logic;
  signal trigger        : std_logic;
  signal led_idle       : std_logic;
  signal test           : std_logic := '0';  --test

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

  clk <= not clk after clk_period / 2;
  uart_clk <= not uart_clk after uart_clk_period / 2;

  dut : entity work.top
  port map (
    clk => clk,
    rst => rst,
    trigger => trigger,
    uart_rx => uart_rx,
    uart_tx => uart_tx,
    led_idle => led_idle
  );

  stim : process
  begin
    rst <= '0';
    wait for 10*clk_period;
    rst <= '1';
    wait for 10*clk_period;

    -- set x0 to 1 and x1 to 10 adn m to 12
    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"40", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    for i in 0 to (3 * 4) - 1 loop
        if i = 0 then 
          tx_byte_p(std_ulogic_vector(to_unsigned(1, 8)), uart_rxd_o => uart_rx);
        elsif i = 4 then 
          tx_byte_p(std_ulogic_vector(to_unsigned(10, 8)), uart_rxd_o => uart_rx);
        elsif i = 8 then
          tx_byte_p(std_ulogic_vector(to_unsigned(12, 8)), uart_rxd_o => uart_rx);
        else
          tx_byte_p(std_ulogic_vector(to_unsigned(0, 8)), uart_rxd_o => uart_rx);
        end if;
      wait for uart_clk_period;
    end loop;

    wait for 10 * uart_clk_period;

    -- try to read data of x0 and x1 and m
    tx_byte_p(x"02", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"40", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;

    wait for 500*uart_clk_period;

    -- start lut calculation
    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"20", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"01", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"01", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    for i in 0 to 2 loop
      tx_byte_p(x"00", uart_rxd_o => uart_rx);
      wait for uart_clk_period;
    end loop;

    test <= '1';
    wait for 10 * uart_clk_period;

    -- read lut output from status memory
    tx_byte_p(x"02", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"10", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"01", uart_rxd_o => uart_rx);
    wait for uart_clk_period;

    wait for 500*uart_clk_period;

    report "SIMULATION FINSIHED" severity failure;
    wait;
  end process;

end architecture;
