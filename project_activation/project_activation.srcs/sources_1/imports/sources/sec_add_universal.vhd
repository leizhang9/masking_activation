library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity sec_add_universal is
  port (
    clk : in std_logic;
    rst : in std_logic;
    start : in std_logic;
    x   : in std_logic_vector(n_bit - 1 downto 0);
    y   : in std_logic_vector(n_bit - 1 downto 0);
    mx  : in std_logic_vector(n_bit - 1 downto 0);
    my  : in std_logic_vector(n_bit - 1 downto 0);
    r0  : in std_logic_vector(n_bit - 2 downto 0);
    r1  : in std_logic_vector(n_bit - 2 downto 0);
    r2  : in std_logic_vector(n_bit - 2 downto 0);
    done : out std_logic;
    z0  : out std_logic_vector(n_bit - 1 downto 0);
    z1  : out std_logic_vector(n_bit - 1 downto 0)
  );
end entity;

architecture behavioral of sec_add_universal is

  component m_dom_and is
    port (
      clk       : in std_logic;
      rst       : in std_logic;
      en        : in std_logic;
      x         : in std_logic_vector(1 downto 0);
      y         : in std_logic_vector(1 downto 0);
      r         : in std_logic;
      z         : out std_logic_vector(1 downto 0)
    );
  end component;

  type state is (RESET, IDLE, PROC, CONV_COMPL, CONV_DONE);
  signal c_state : state;
  signal n_state : state;

  signal count : std_logic;
  signal en_count : std_logic;

  signal and_stage_en : std_logic_vector(n_bit - 2 downto 0);

  type s_vector is array (0 to n_bit - 2) of std_logic_vector(1 downto 0);
  signal z_int : s_vector;
  signal z_int1 : s_vector;
  signal z_int2 : s_vector;
  --
  signal c0 : std_logic_vector(n_bit - 1 downto 0);
  signal c1 : std_logic_vector(n_bit - 1 downto 0);

  signal xy0 : std_logic_vector(n_bit - 2 downto 0);
  signal xy1 : std_logic_vector(n_bit - 2 downto 0);

  signal xc0 : std_logic_vector(n_bit - 2 downto 0);
  signal xc1 : std_logic_vector(n_bit - 2 downto 0);

  signal yc0 : std_logic_vector(n_bit - 2 downto 0);
  signal yc1 : std_logic_vector(n_bit - 2 downto 0);

  signal x0 : std_logic_vector(n_bit - 1 downto 0);
  signal x1 : std_logic_vector(n_bit - 1 downto 0);
  signal y0 : std_logic_vector(n_bit - 1 downto 0);
  signal y1 : std_logic_vector(n_bit - 1 downto 0);

  signal r0_buf : std_logic_vector(n_bit - 2 downto 0);
  signal r1_buf : std_logic_vector(n_bit - 2 downto 0);
  signal r2_buf : std_logic_vector(n_bit - 2 downto 0);

  attribute DONT_TOUCH : string;
  attribute keep : string;

  attribute keep of x0 : signal is "true";
  attribute keep of x1 : signal is "true";
  attribute keep of y0 : signal is "true";
  attribute keep of y1 : signal is "true";

  attribute keep of xy0 : signal is "true";
  attribute keep of xy1 : signal is "true";
  attribute keep of r0_buf : signal is "true";
  attribute keep of r1_buf : signal is "true";
  attribute keep of r2_buf : signal is "true";
  attribute keep of xc0 : signal is "true";
  attribute keep of xc1 : signal is "true";
  attribute keep of c0  : signal is "true";
  attribute keep of c1  : signal is "true";
  attribute keep of yc0 : signal is "true";
  attribute keep of yc1 : signal is "true";

  attribute keep of and_stage_en : signal is "true";
  attribute keep of c_state : signal is "true";
  attribute keep of n_state : signal is "true";


  attribute DONT_TOUCH of xyc   : label is "true";
  --attribute DONT_TOUCH of reg   : label is "true";
  attribute DONT_TOUCH of m_dom_and : component is "true";



begin

  z_out : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        z0 <= (others => '0');
        z1 <= (others => '0');
      elsif c_state = CONV_COMPL then
        z0 <= x0 xor y0 xor c0;
        z1 <= x1 xor y1 xor c1;
      end if;
    end if;
  end process;

  carry : process(xy0, xy1, xc0, xc1, yc0, yc1)
  begin
    c0(0) <= '0';
    c1(0) <= '0';
    c_loop : for i in 0 to n_bit - 2 loop
      c0(i + 1) <= xy0(i) xor xc0(i) xor yc0(i);
      c1(i + 1) <= xy1(i) xor xc1(i) xor yc1(i);
    end loop;
  end process;

  and_stage : process(clk)
  variable tmp : unsigned(n_bit - 2 downto 0) := (others => '0');
  attribute keep of tmp : variable is "true";
  begin
    -- if clk'event and clk = '1' then
    --   if rst = '1' then
    --     and_stage_en <= (others => '0');
    --   else
    --     if start = '1' then
    --       and_stage_en <= std_logic_vector(to_unsigned(1, n_bit - 1));
    --     elsif en_count = '1' and count = '1' then
    --       and_stage_en <= std_logic_vector(shift_left(unsigned(and_stage_en), 1));
    --     elsif c_state /= IDLE then
    --       and_stage_en <= and_stage_en;
    --     else
    --       and_stage_en <= (others => '0');
    --     end if;
    --   end if;
    -- end if;
    if clk'event and clk = '1' then
      if rst = '1' then
        tmp := (others => '0');
      else
        if start = '1' then
          tmp := to_unsigned(1, n_bit - 1);
        elsif en_count = '1' and count = '1' then
          tmp := shift_left(unsigned(and_stage_en), 1);
          tmp := tmp xor to_unsigned(1, n_bit - 1);
        elsif c_state /= IDLE then
          tmp := tmp;
        else
          tmp := (others => '0');
        end if;
      end if;
      and_stage_en <= std_logic_vector(tmp);
    end if;
  end process;

  buf : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        r0_buf <= (others => '0');
        r1_buf <= (others => '0');
        r2_buf <= (others => '0');
      else
        r0_buf <= r0;
        r1_buf <= r1;
        r2_buf <= r2;
      end if;
    end if;
  end process;

  cnt : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' or c_state = IDLE then
        count <= '0';
      elsif en_count = '1' then
        count <= not count;
      end if;
    end if;
  end process;

  out_logic : process(c_state)
  begin
    case( c_state ) is
      when PROC =>
        en_count <= '1';
        done <= '0';
      when CONV_COMPL =>
        en_count <= '0';
        done <= '0';
      when CONV_DONE =>
        en_count <= '0';
        done <= '1';
      when others =>
        en_count <= '0';
        done <= '0';
    end case;
  end process;

  ns_logic : process(c_state, rst, start, and_stage_en, count)
  begin
    case( c_state ) is
      when RESET =>
        if rst = '1' then
          n_state <= RESET;
        else
          n_state <= IDLE;
        end if;
      when IDLE =>
        if start = '1' then
          n_state <= PROC;
        else
          n_state <= IDLE;
        end if;
      when PROC =>
        if and_stage_en(n_bit - 2) = '1' and count = '1' then
          n_state <= CONV_COMPL;
        else
          n_state <= PROC;
        end if;
      when CONV_COMPL =>
        n_state <= CONV_DONE;
      when CONV_DONE =>
        n_state <= IDLE;
      when others =>
        n_state <= IDLE;
    end case;
  end process;

  state_mem : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        c_state <= RESET;
      else
        c_state <= n_state;
      end if;
    end if;
  end process;

  reg : process(clk)
  begin
    if clk'event and clk = '0' then
      if rst = '1' then
        x0 <= (others => '0');
        x1 <= (others => '0');
        y0 <= (others => '0');
        y1 <= (others => '0');
      elsif start = '1' then
        x0 <= x;
        x1 <= mx;
        y0 <= y;
        y1 <= my;
      end if;
    end if;
  end process;

  xy_gen : for i in 0 to n_bit - 2 generate
    sec_and_xy : m_dom_and
      port map (
        clk => clk,
        rst => rst,
        en => and_stage_en(i),
        x => x0(i) & x1(i),
        y => y0(i) & y1(i),
        r => r0_buf(i),
        z => z_int(i)
      );
  end generate;

  -- sec_and_xy0 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(0),
  --     x => x0(0) & x1(0),
  --     y => y0(0) & y1(0),
  --     r => r0_buf(0),
  --     z => z_int(0)
  --   );
  -- sec_and_xy1 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(1),
  --     x => x0(1) & x1(1),
  --     y => y0(1) & y1(1),
  --     r => r0_buf(1),
  --     z => z_int(1)
  --   );
  -- sec_and_xy2 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(2),
  --     x => x0(2) & x1(2),
  --     y => y0(2) & y1(2),
  --     r => r0_buf(2),
  --     z => z_int(2)
  --   );
  -- sec_and_xy3 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(3),
  --     x => x0(3) & x1(3),
  --     y => y0(3) & y1(3),
  --     r => r0_buf(3),
  --     z => z_int(3)
  --   );
  -- sec_and_xy4 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(4),
  --     x => x0(4) & x1(4),
  --     y => y0(4) & y1(4),
  --     r => r0_buf(4),
  --     z => z_int(4)
  --   );
  -- sec_and_xy5 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(5),
  --     x => x0(5) & x1(5),
  --     y => y0(5) & y1(5),
  --     r => r0_buf(5),
  --     z => z_int(5)
  --   );
  -- sec_and_xy6 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(6),
  --     x => x0(6) & x1(6),
  --     y => y0(6) & y1(6),
  --     r => r0_buf(6),
  --     z => z_int(6)
  --   );
  --
  -- sec_and_xc0 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(0),
  --     x => x0(0) & x1(0),
  --     y => c0(0) & c1(0),
  --     r => r1_buf(0),
  --     z => z_int1(0)
  --   );
  -- sec_and_xc1 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(1),
  --     x => x0(1) & x1(1),
  --     y => c0(1) & c1(1),
  --     r => r1_buf(1),
  --     z => z_int1(1)
  --   );
  -- sec_and_xc2 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(2),
  --     x => x0(2) & x1(2),
  --     y => c0(2) & c1(2),
  --     r => r1_buf(2),
  --     z => z_int1(2)
  --   );
  -- sec_and_xc3 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(3),
  --     x => x0(3) & x1(3),
  --     y => c0(3) & c1(3),
  --     r => r1_buf(3),
  --     z => z_int1(3)
  --   );
  -- sec_and_xc4 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(4),
  --     x => x0(4) & x1(4),
  --     y => c0(4) & c1(4),
  --     r => r1_buf(4),
  --     z => z_int1(4)
  --   );
  -- sec_and_xc5 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(5),
  --     x => x0(5) & x1(5),
  --     y => c0(5) & c1(5),
  --     r => r1_buf(5),
  --     z => z_int1(5)
  --   );
  -- sec_and_xc6 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(6),
  --     x => x0(6) & x1(6),
  --     y => c0(6) & c1(6),
  --     r => r1_buf(6),
  --     z => z_int1(6)
  --   );
  --
  -- sec_and_yc0 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(0),
  --     x => y0(0) & y1(0),
  --     y => c0(0) & c1(0),
  --     r => r2_buf(0),
  --     z => z_int2(0)
  --   );
  -- sec_and_yc1 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(1),
  --     x => y0(1) & y1(1),
  --     y => c0(1) & c1(1),
  --     r => r2_buf(1),
  --     z => z_int2(1)
  --   );
  -- sec_and_yc2 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(2),
  --     x => y0(2) & y1(2),
  --     y => c0(2) & c1(2),
  --     r => r2_buf(2),
  --     z => z_int2(2)
  --   );
  -- sec_and_yc3 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(3),
  --     x => y0(3) & y1(3),
  --     y => c0(3) & c1(3),
  --     r => r2_buf(3),
  --     z => z_int2(3)
  --   );
  -- sec_and_yc4 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(4),
  --     x => y0(4) & y1(4),
  --     y => c0(4) & c1(4),
  --     r => r2_buf(4),
  --     z => z_int2(4)
  --   );
  -- sec_and_yc5 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(5),
  --     x => y0(5) & y1(5),
  --     y => c0(5) & c1(5),
  --     r => r2_buf(5),
  --     z => z_int2(5)
  --   );
  -- sec_and_yc6 : sec_and
  --   port map (
  --     clk => clk,
  --     rst => rst,
  --     en => and_stage_en(6),
  --     x => y0(6) & y1(6),
  --     y => c0(6) & c1(6),
  --     r => r2_buf(6),
  --     z => z_int2(6)
  --   );

  xc_gen : for i in 0 to n_bit - 2 generate
    sec_and_xc : m_dom_and
      port map (
        clk => clk,
        rst => rst,
        en => and_stage_en(i),
        x => x0(i) & x1(i),
        y => c0(i) & c1(i),
        r => r1_buf(i),
        z => z_int1(i)
      );
  end generate;

  yc_gen : for i in 0 to n_bit - 2 generate
    sec_and_yc : m_dom_and
      port map (
        clk => clk,
        rst => rst,
        en => and_stage_en(i),
        x => y0(i) & y1(i),
        y => c0(i) & c1(i),
        r => r2_buf(i),
        z => z_int2(i)
      );
  end generate;

  xyc : process(z_int, z_int1, z_int2)
  variable tmp0 : std_logic_vector(n_bit - 2 downto 0);
  variable tmp1 : std_logic_vector(n_bit - 2 downto 0);
  variable tmp2 : std_logic_vector(n_bit - 2 downto 0);
  variable tmp3 : std_logic_vector(n_bit - 2 downto 0);
  variable tmp4 : std_logic_vector(n_bit - 2 downto 0);
  variable tmp5 : std_logic_vector(n_bit - 2 downto 0);
  begin
    xyc_loop : for i in xy0'range loop
      tmp0(i) := z_int(i)(0);
      tmp1(i) := z_int(i)(1);
      tmp2(i) := z_int1(i)(0);
      tmp3(i) := z_int1(i)(1);
      tmp4(i) := z_int2(i)(0);
      tmp5(i) := z_int2(i)(1);
    end loop;
    xy0 <= tmp0;
    xy1 <= tmp1;
    xc0 <= tmp2;
    xc1 <= tmp3;
    yc0 <= tmp4;
    yc1 <= tmp5;
    -- xy0 <= z_int(6)(0) & z_int(5)(0) & z_int(4)(0) & z_int(3)(0) & z_int(2)(0) & z_int(1)(0) & z_int(0)(0);
    -- xy1 <= z_int(6)(1) & z_int(5)(1) & z_int(4)(1) & z_int(3)(1) & z_int(2)(1) & z_int(1)(1) & z_int(0)(1);
    -- xc0 <= z_int1(6)(0) & z_int1(5)(0) & z_int1(4)(0) & z_int1(3)(0) & z_int1(2)(0) & z_int1(1)(0) & z_int1(0)(0);
    -- xc1 <= z_int1(6)(1) & z_int1(5)(1) & z_int1(4)(1) & z_int1(3)(1) & z_int1(2)(1) & z_int1(1)(1) & z_int1(0)(1);
    -- yc0 <= z_int2(6)(0) & z_int2(5)(0) & z_int2(4)(0) & z_int2(3)(0) & z_int2(2)(0) & z_int2(1)(0) & z_int2(0)(0);
    -- yc1 <= z_int2(6)(1) & z_int2(5)(1) & z_int2(4)(1) & z_int2(3)(1) & z_int2(2)(1) & z_int2(1)(1) & z_int2(0)(1);
  end process;

end architecture;
